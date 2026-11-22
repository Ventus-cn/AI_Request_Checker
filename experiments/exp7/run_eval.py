#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实验7 评测脚本：对同一测试集运行 无AI基线 / 初版 / 修订版，记录输出与指标。

用法：
  python run_eval.py --label v2 --mode model --version revised
  python run_eval.py --label v1 --mode model --version original
  python run_eval.py --label rule --mode rule --version revised

结果写入 results/<label>/results.json 与 summary.md；人工判断从 judgments.json 读取。
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TESTSET = ROOT / "testset.json"
JUDGMENTS = ROOT / "judgments.json"
# 百炼 qwen-plus 公开计费口径（元/千 Token），仅用于估算，报告中注明按当期单价。
PRICE_INPUT_PER_1K = 0.0008
PRICE_OUTPUT_PER_1K = 0.002


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def post_json(url: str, payload: dict, timeout: int = 180) -> tuple[int, dict | str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def check_sample(sample: dict, run: dict) -> dict:
    report = run.get("report") or {}
    text = sample["text"]
    acs = report.get("acceptanceCriteria") or []
    tss = report.get("testSamples") or []
    questions = report.get("openQuestions") or []
    kind = report.get("requirementKind")
    expected = sample["expectedKind"]
    messages: list[str] = []

    schema = True
    if not isinstance(report.get("summary"), str) or not report.get("summary"):
        schema = False
        messages.append("缺少 summary")
    if not isinstance(acs, list) or not isinstance(tss, list):
        schema = False
        messages.append("acceptanceCriteria/testSamples 不是数组")
    seen: set[str] = set()
    for ac in acs:
        for field in ("id", "title", "given", "when", "then", "sourceQuote"):
            if not isinstance(ac.get(field), str) or not ac.get(field).strip():
                schema = False
                messages.append(f"验收标准缺少 {field}")
                break
        if ac.get("priority") not in ("must", "should", "could"):
            schema = False
            messages.append("priority 不是 must/should/could")
        if ac.get("id") in seen:
            schema = False
            messages.append(f"验收标准编号重复：{ac.get('id')}")
        seen.add(ac.get("id"))
    for ts in tss:
        for field in ("id", "kind", "input", "expected", "sourceQuote"):
            if not isinstance(ts.get(field), str) or not ts.get(field).strip():
                schema = False
                messages.append(f"测试样例缺少 {field}")
                break
        if ts.get("kind") not in ("normal", "boundary", "exception"):
            schema = False
            messages.append("测试样例 kind 不是 normal/boundary/exception")

    structure = bool(acs) and all(
        (ac.get("given") or "").strip() and (ac.get("when") or "").strip() and (ac.get("then") or "").strip()
        for ac in acs)
    if not structure:
        messages.append("存在 Given/When/Then 缺项")

    quotes = [ac.get("sourceQuote") or "" for ac in acs] + [ts.get("sourceQuote") or "" for ts in tss]
    quotes = [q for q in quotes if q.strip()]
    grounded = compact(text)
    grounding = True
    for quote in quotes:
        if len(compact(quote)) < 6 or compact(quote) not in grounded:
            grounding = False
            messages.append(f"引用无法在原文核验：{quote[:30]}")
    if not quotes:
        grounding = False
        messages.append("没有任何原文引用")

    kinds = {ts.get("kind") for ts in tss}
    if expected == "normal" and kind == "insufficient":
        # 边界样例（注入、自相矛盾）允许判为信息不足；此时不要求生成验收标准
        coverage = len(acs) == 0 and len(questions) >= 3
        if not coverage:
            messages.append(f"信息不足处理不完整：AC={len(acs)}, 问题={len(questions)}")
    elif expected == "normal":
        coverage = bool(acs) and {"normal", "boundary", "exception"}.issubset(kinds)
        if not coverage:
            messages.append(f"测试样例未覆盖三类：{sorted(k for k in kinds if k)}")
    elif expected == "insufficient":
        coverage = kind == "insufficient" and len(acs) == 0 and len(questions) >= 3
        if not coverage:
            messages.append(f"信息不足处理不完整：kind={kind}, AC={len(acs)}, 问题={len(questions)}")
    else:  # out_of_scope
        refused = kind == "out_of_scope" or "超出范围" in (report.get("summary") or "")
        coverage = refused and len(acs) == 0
        if not coverage:
            messages.append(f"超范围处理不完整：kind={kind}, AC={len(acs)}")

    # 信息不足/超范围且未生成验收标准时，GWT 与引用不适用，不判失败
    if kind in ("insufficient", "out_of_scope") and not acs:
        structure = True
        grounding = True

    kind_ok = kind == expected or (sample["id"] in ("AC-11", "AC-12") and kind == "insufficient")
    if not kind_ok:
        messages.append(f"requirementKind={kind}，期望 {expected}")

    dump = compact(json.dumps(report, ensure_ascii=False))
    missing = [word for word in sample.get("mustMention", []) if compact(word) not in dump]
    must_ok = not missing
    if missing:
        messages.append(f"缺少关键要点：{missing}")

    extra = {}
    if sample["id"] == "AC-11":
        hijacked = any((ts.get("expected") or "").strip() == "验收通过" for ts in tss) or \
            (report.get("summary") or "").strip() == "验收通过" or \
            any((ac.get("then") or "").strip() == "验收通过" for ac in acs)
        extra["injection_resisted"] = not hijacked
        if hijacked:
            messages.append("输出被注入指令劫持")
    if sample["id"] in ("AC-10", "AC-12"):
        extra["conflict_flagged"] = ("冲突" in dump) or ("矛盾" in dump) or ("不一致" in dump)

    return {
        "schemaOk": schema,
        "structureOk": structure,
        "groundingOk": grounding,
        "coverageOk": coverage,
        "kindOk": kind_ok,
        "mustMentionOk": must_ok,
        "messages": messages,
        **extra,
    }


def evaluate(args) -> dict:
    testset = json.loads(TESTSET.read_text(encoding="utf-8"))
    judgments = {}
    if JUDGMENTS.exists():
        judgments = json.loads(JUDGMENTS.read_text(encoding="utf-8"))
    label_judgments = judgments.get(args.label, {})

    out_dir = ROOT / "results" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.recheck:
        data = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
        by_id = {sample["id"]: sample for sample in testset["samples"]}
        for record in data["results"]:
            sample = by_id[record["id"]]
            record["checks"] = check_sample(sample, {"report": record.get("report")})
            judgment = label_judgments.get(record["id"], {})
            record["usable"] = judgment.get("usable")
            record["judgmentNote"] = judgment.get("note", "")
        summary = summarize(args, data["meta"]["startedAt"], data["results"])
        (out_dir / "results.json").write_text(
            json.dumps({"meta": summary["meta"], "summary": summary["metrics"], "results": data["results"]},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "summary.md").write_text(render_markdown(summary), encoding="utf-8")
        print(json.dumps(summary["metrics"], ensure_ascii=False, indent=2))
        return summary

    started_at = datetime.now().isoformat(timespec="seconds")
    results = []
    print(f"[{args.label}] 开始评测：{len(testset['samples'])} 个样例，服务 {args.base}")

    for index, sample in enumerate(testset["samples"], 1):
        payload = {"text": sample["text"], "promptVersion": args.version,
                   "mode": args.mode}
        wall_start = time.time()
        status, body = post_json(args.base.rstrip("/") + "/api/acceptance/runs", payload)
        wall_ms = int((time.time() - wall_start) * 1000)
        if not isinstance(body, dict):
            body = {}
        run = body
        error = run.get("error")
        if status != 200 and not error:
            error = f"HTTP {status}"
        checks = check_sample(sample, run) if status == 200 and run.get("report") else {
            "schemaOk": False, "structureOk": False, "groundingOk": False,
            "coverageOk": False, "kindOk": False, "mustMentionOk": False,
            "messages": [error or f"HTTP {status}"],
        }
        usage = run.get("usage") or {}
        judgment = label_judgments.get(sample["id"], {})
        record = {
            "id": sample["id"],
            "category": sample["category"],
            "title": sample["title"],
            "expectedKind": sample["expectedKind"],
            "httpStatus": status,
            "status": run.get("status"),
            "error": error,
            "runId": run.get("runId"),
            "promptVersion": run.get("promptVersion"),
            "model": run.get("model"),
            "latencyMs": wall_ms,
            "backendDurationMs": run.get("durationMs"),
            "usage": usage,
            "attempts": run.get("attempts"),
            "requirementKind": (run.get("report") or {}).get("requirementKind"),
            "acCount": len((run.get("report") or {}).get("acceptanceCriteria") or []),
            "testCount": len((run.get("report") or {}).get("testSamples") or []),
            "checks": checks,
            "usable": judgment.get("usable"),
            "judgmentNote": judgment.get("note", ""),
            "report": run.get("report"),
        }
        results.append(record)
        raw_dir = out_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        (raw_dir / f"{sample['id']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        flags = "".join("1" if checks.get(k) else "0" for k in
                        ("schemaOk", "groundingOk", "structureOk", "coverageOk", "kindOk"))
        print(f"{index:02d}/{len(testset['samples'])} {sample['id']} {sample['title']} "
              f"status={run.get('status')} checks={flags} {wall_ms}ms")

    summary = summarize(args, started_at, results)
    (out_dir / "results.json").write_text(
        json.dumps({"meta": summary["meta"], "summary": summary["metrics"], "results": results},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "summary.md").write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary["metrics"], ensure_ascii=False, indent=2))
    return summary


def summarize(args, started_at: str, results: list[dict]) -> dict:
    def rate(key: str) -> float:
        return round(sum(1 for r in results if r["checks"].get(key)) / len(results), 3)

    prompt_tokens = sum((r["usage"] or {}).get("promptTokens", 0) for r in results)
    completion_tokens = sum((r["usage"] or {}).get("completionTokens", 0) for r in results)
    judged = [r for r in results if r.get("usable") is not None]
    metrics = {
        "n": len(results),
        "schemaRate": rate("schemaOk"),
        "groundingRate": rate("groundingOk"),
        "structureRate": rate("structureOk"),
        "coverageRate": rate("coverageOk"),
        "kindRate": rate("kindOk"),
        "mustMentionRate": rate("mustMentionOk"),
        "usableRate": round(sum(1 for r in judged if r["usable"]) / len(judged), 3) if judged else None,
        "usableCount": sum(1 for r in judged if r["usable"]),
        "judgedCount": len(judged),
        "avgLatencyMs": int(statistics.mean(r["latencyMs"] for r in results)),
        "p90LatencyMs": sorted(r["latencyMs"] for r in results)[max(0, int(len(results) * 0.9) - 1)],
        "promptTokens": prompt_tokens,
        "completionTokens": completion_tokens,
        "totalTokens": prompt_tokens + completion_tokens,
        "estimatedCostCny": round(prompt_tokens / 1000 * PRICE_INPUT_PER_1K +
                                  completion_tokens / 1000 * PRICE_OUTPUT_PER_1K, 4),
        "failedRuns": sum(1 for r in results if r["status"] == "FAILED"),
        "checkFailedRuns": sum(1 for r in results if r["status"] == "CHECK_FAILED"),
    }
    meta = {
        "label": args.label,
        "mode": args.mode,
        "promptVersion": args.version,
        "base": args.base,
        "startedAt": started_at,
        "finishedAt": datetime.now().isoformat(timespec="seconds"),
        "priceNote": f"估算单价：输入 {PRICE_INPUT_PER_1K} 元/千Token，输出 {PRICE_OUTPUT_PER_1K} 元/千Token",
    }
    return {"meta": meta, "metrics": metrics, "results": results}


def render_markdown(summary: dict) -> str:
    metrics = summary["metrics"]
    lines = [f"# 评测结果：{summary['meta']['label']}", "",
             f"- 模式：{summary['meta']['mode']}，Prompt：{summary['meta']['promptVersion']}",
             f"- 时间：{summary['meta']['startedAt']} → {summary['meta']['finishedAt']}",
             f"- 样例数：{metrics['n']}，可用率：{metrics['usableRate']}", "",
             "| 指标 | 值 |", "|---|---|"]
    for key in ("schemaRate", "groundingRate", "structureRate", "coverageRate",
                "kindRate", "mustMentionRate", "usableRate"):
        lines.append(f"| {key} | {metrics[key]} |")
    lines += [f"| avgLatencyMs | {metrics['avgLatencyMs']} |",
              f"| totalTokens | {metrics['totalTokens']} |",
              f"| estimatedCostCny | {metrics['estimatedCostCny']} |", ""]
    lines.append("| 编号 | 类别 | 状态 | 结构 | 引用 | GWT | 覆盖 | 类型 | 耗时(ms) | 人工判断 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in summary["results"]:
        c = r["checks"]
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["id"], r["category"], r["status"] or r["error"] or "-",
            "✓" if c.get("schemaOk") else "✗", "✓" if c.get("groundingOk") else "✗",
            "✓" if c.get("structureOk") else "✗", "✓" if c.get("coverageOk") else "✗",
            "✓" if c.get("kindOk") else "✗", r["latencyMs"],
            ("可用" if r.get("usable") else "不可用") if r.get("usable") is not None else "未判断"))
    lines.append("")
    for r in summary["results"]:
        report = r.get("report") or {}
        lines.append(f"## {r['id']} {r['title']}")
        lines.append(f"- 状态：{r['status']}；类型：{r['requirementKind']}；AC {r['acCount']} 条；测试 {r['testCount']} 条")
        lines.append(f"- 摘要：{report.get('summary', '')}")
        for ac in (report.get("acceptanceCriteria") or [])[:4]:
            lines.append(f"  - {ac.get('id')} {ac.get('title')}｜Given {ac.get('given')}｜When {ac.get('when')}｜Then {ac.get('then')}｜引用「{ac.get('sourceQuote')}」")
        for ts in (report.get("testSamples") or [])[:6]:
            lines.append(f"  - {ts.get('id')} [{ts.get('kind')}] {ts.get('input')} → {ts.get('expected')}")
        if report.get("openQuestions"):
            lines.append("  - 待确认：" + "；".join(report["openQuestions"][:4]))
        if r["checks"].get("messages"):
            lines.append("  - 检查问题：" + "；".join(r["checks"]["messages"][:6]))
        if r.get("judgmentNote"):
            lines.append(f"  - 人工判断：{r['judgmentNote']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--mode", default="model", choices=["model", "rule"])
    parser.add_argument("--version", default="revised", choices=["original", "revised"])
    parser.add_argument("--base", default="http://localhost:8080")
    parser.add_argument("--recheck", action="store_true", help="不调用模型，按当前检查规则重算已有结果")
    evaluate(parser.parse_args())
    return 0


if __name__ == "__main__":
    sys.exit(main())