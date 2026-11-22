#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成报告用的数据流图与评测看板（HTML，随后由 shoot.mjs 截图）。"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP7 = ROOT / "experiments" / "exp7"
FIG = ROOT / "实验文档" / "TEST7" / "图"
FIG.mkdir(parents=True, exist_ok=True)

LABELS = [("rule", "无 AI 基线", "#8a93a8"), ("v1", "初版 v1", "#4f7fd8"), ("v2", "修订版 v2", "#2e9e74")]


def load(label: str):
    path = EXP7 / "results" / label / "results.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def flow_html() -> str:
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#fff;color:#1e2637;font-family:"Microsoft YaHei","PingFang SC",sans-serif;padding:34px 40px 28px}
h1{font-size:21px;letter-spacing:.5px;margin-bottom:4px}
.sub{font-size:11px;color:#66708a;margin-bottom:24px}
.canvas{width:1220px}
.flow{display:flex;flex-direction:column;align-items:center;gap:0}
.row{display:flex;align-items:stretch;gap:14px;justify-content:center;width:100%}
.node{background:#f4f7fd;border:1px solid #c9d4ea;border-left:4px solid #4f7fd8;border-radius:8px;padding:10px 14px;min-width:250px}
.node b{display:block;font-size:13px;margin-bottom:4px}
.node span{display:block;font-size:10.5px;line-height:1.65;color:#556079}
.node.model{border-left-color:#8b5cf6;background:#f7f3ff;border-color:#d8cbf2}
.node.check{border-left-color:#d79a2b;background:#fffaef;border-color:#ecd9b3}
.node.ok{border-left-color:#2e9e74;background:#f0fbf6;border-color:#bfe6d7}
.node.fail{border-left-color:#d05a6a;background:#fdf2f4;border-color:#efc7ce}
.node.store{border-left-color:#2f7fb8;background:#f1f8fd;border-color:#c2dfef}
.arrow{height:26px;display:grid;place-items:center;color:#8a96ad;font-size:15px;line-height:1}
.branch{display:grid;grid-template-columns:1fr 1fr;gap:26px;width:100%;margin-top:8px}
.branch .col{display:flex;flex-direction:column;gap:10px}
.branch .title{font-size:10px;color:#7a8499;letter-spacing:.5px;text-align:center}
.side{border:1.5px dashed #b4a6e0;background:#faf8ff;border-radius:8px;padding:10px 14px;margin-top:22px;color:#5b4a8a}
.side b{font-size:11.5px}
.side span{display:block;font-size:10px;line-height:1.7;margin-top:3px;color:#6d6390}
.legend{display:flex;gap:22px;margin-top:18px;font-size:10px;color:#66708a;border-top:1px solid #e2e8f2;padding-top:12px}
.legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px}
.two{display:grid;grid-template-columns:1fr 320px;gap:24px;align-items:start}
</style></head><body><div class="canvas">
<h1>验收标准生成原型：数据流与端到端链路</h1>
<div class="sub">输入 → 预处理 → 模型 → 解析与程序检查 → 展示/保存；虚线框为后续接入基础软件的位置</div>
<div class="two">
<div class="flow">
  <div class="row"><div class="node input"><b>① 用户输入</b><span>需求原文（≤3000 字），来源：页面粘贴或测试集；拒绝空输入与超长输入</span></div></div>
  <div class="arrow">↓</div>
  <div class="row"><div class="node"><b>② 预处理</b><span>空白规范化、长度校验、非软件需求范围预判（采购/付款/股票等）；规则命中直接拒绝，不调用模型</span></div></div>
  <div class="arrow">↓</div>
  <div class="row"><div class="node model"><b>③ 模型调用 · qwen-plus</b><span>system Prompt（v1 初版 / v2 修订版）+ 需求原文；v2 修复轮次追加上一版输出与检查错误</span></div></div>
  <div class="arrow">↓</div>
  <div class="row"><div class="node"><b>④ 解析与字段映射</b><span>去除代码围栏、截取 JSON、映射 requirementKind / 验收标准 / 测试样例 / 待确认问题</span></div></div>
  <div class="arrow">↓</div>
  <div class="row"><div class="node check"><b>⑤ 程序检查（v2）</b><span>结构合法 · 原文引用逐字核验 · Given/When/Then 完整 · 正常/边界/异常覆盖 · 类型判定</span></div></div>
  <div class="branch">
    <div class="col"><div class="title">检查通过</div><div class="node ok"><b>⑥ 展示与保存</b><span>页面展示验收标准 / 测试样例 / 待确认问题；写入 runs/&lt;runId&gt;.jsonl 与 .json</span></div></div>
    <div class="col"><div class="title">检查不通过且尝试 &lt; 3</div><div class="node fail"><b>⑥′ 有限修复</b><span>把检查错误作为反馈追加到上下文，要求模型重写；连续失败返回 CHECK_FAILED</span></div></div>
  </div>
  <div class="arrow">↓</div>
  <div class="row"><div class="node store"><b>⑦ 评测与对比</b><span>同一测试集（12 例）分别运行 基线 / 初版 / 修订版，记录输出、检查、耗时与 Token</span></div></div>
</div>
<div>
  <div class="side"><b>准备与基础软件连接的位置</b><span>① 从「审查档案」选择已保存的需求，作为输入来源；<br>② 生成结果回写为档案的一个版本，或作为验收标准字段参与报告导出；<br>③ 当前实验不要求完成集成，接口已按 REST 设计（POST /api/acceptance/runs）。</span></div>
  <div class="side" style="border-color:#c9d4ea;background:#f8fafd;color:#4b5a76"><b>集中配置</b><span>模型名、温度、max_tokens、超时、最大尝试次数、日志目录集中在 application.yml 的 app.acceptance；两版 Prompt 分别放在 resources/acceptance/prompt-initial.txt 与 prompt-revised.txt；API Key 只从环境变量读取。</span></div>
  <div class="side" style="border-color:#ecd9b3;background:#fffdf7;color:#7a5a1f"><b>无 AI 基线</b><span>按中文句号切句，套用固定模板生成 1 条测试样例；不判断信息是否充分，不做引用与覆盖检查，用于说明“有/无程序校验”的差异。</span></div>
</div>
</div>
<div class="legend"><span><i style="background:#4f7fd8"></i>业务步骤</span><span><i style="background:#8b5cf6"></i>模型调用</span><span><i style="background:#d79a2b"></i>程序检查</span><span><i style="background:#2e9e74"></i>通过分支</span><span><i style="background:#d05a6a"></i>修复分支</span></div>
</div></body></html>"""


def metric_rows(data: dict) -> dict:
    m = data["summary"]
    return {
        "program": round(sum(1 for r in data["results"]
                             if all(r["checks"].get(k) for k in
                                    ("schemaOk", "groundingOk", "structureOk", "coverageOk"))) / len(data["results"]), 3),
        "schema": m["schemaRate"], "grounding": m["groundingRate"],
        "coverage": m["coverageRate"], "kind": m["kindRate"],
        "latency": m["avgLatencyMs"], "tokens": m["totalTokens"],
        "cost": m["estimatedCostCny"],
        "usable": m.get("usableRate"),
    }


def dashboard_html() -> str:
    datasets = {label: load(label) for label, _, _ in LABELS}
    if any(v is None for v in datasets.values()):
        missing = [k for k, v in datasets.items() if v is None]
        return f"<html><body><h1>缺少评测结果：{missing}</h1></body></html>"
    rows = {label: metric_rows(data) for label, data in datasets.items()}

    def pct(value):
        return "—" if value is None else f"{value * 100:.0f}%"

    cards = []
    for label, name, color in LABELS:
        r = rows[label]
        cards.append(f"""<div class="card"><div class="card-title" style="border-color:{color}">{name}</div>
        <div class="big">{pct(r['program'])}<small>程序可接受</small></div>
        <div class="kv"><span>结构合法</span><b>{pct(r['schema'])}</b></div>
        <div class="kv"><span>引用可核验</span><b>{pct(r['grounding'])}</b></div>
        <div class="kv"><span>三类覆盖</span><b>{pct(r['coverage'])}</b></div>
        <div class="kv"><span>类型判定</span><b>{pct(r['kind'])}</b></div>
        <div class="kv"><span>人工可用</span><b>{pct(r['usable'])}</b></div>
        <div class="kv"><span>平均耗时</span><b>{r['latency']} ms</b></div>
        <div class="kv"><span>总 Token</span><b>{r['tokens']}</b></div>
        <div class="kv"><span>估算费用</span><b>¥{r['cost']}</b></div></div>""")

    def bars(key, title):
        parts = []
        for label, name, color in LABELS:
            value = rows[label][key] or 0
            parts.append(f"""<div class="bar-row"><span class="bar-label">{name}</span>
            <div class="bar"><i style="width:{max(value * 100, 1):.0f}%;background:{color}"></i></div>
            <b>{pct(rows[label][key])}</b></div>""")
        return f'<div class="chart"><h3>{title}</h3>{"".join(parts)}</div>'

    ids = [r["id"] for r in datasets["v2"]["results"]]
    table_rows = []
    for sid in ids:
        cells = [f"<td class='id'>{sid}</td>"]
        category = next(r["category"] for r in datasets["v2"]["results"] if r["id"] == sid)
        cells.append(f"<td>{category}</td>")
        for label, _, _ in LABELS:
            rec = next(r for r in datasets[label]["results"] if r["id"] == sid)
            ok = all(rec["checks"].get(k) for k in
                     ("schemaOk", "groundingOk", "structureOk", "coverageOk"))
            cells.append(f"<td class='{'yes' if ok else 'no'}'>{'✓' if ok else '✗'}</td>")
        table_rows.append("<tr>" + "".join(cells) + "</tr>")

    meta = datasets["v2"]["meta"]
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#fff;color:#1e2637;font-family:"Microsoft YaHei","PingFang SC",sans-serif;padding:30px 36px}}
h1{{font-size:21px;margin-bottom:4px}} .sub{{font-size:11px;color:#66708a;margin-bottom:18px}}
.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}}
.card{{border:1px solid #dbe3f0;border-radius:10px;padding:14px 16px;background:#fbfdff}}
.card-title{{font-size:12px;font-weight:700;border-left:4px solid #999;padding-left:8px;margin-bottom:8px}}
.big{{font-size:30px;font-weight:800;color:#1e2637}} .big small{{display:block;font-size:10px;color:#7a8499;font-weight:500;margin-top:2px}}
.kv{{display:flex;justify-content:space-between;font-size:10.5px;color:#66708a;padding:3px 0;border-bottom:1px dashed #edf1f8}}
.kv b{{color:#28324a}}
.charts{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:20px}}
.chart{{border:1px solid #dbe3f0;border-radius:10px;padding:12px 14px}}
.chart h3{{font-size:11.5px;margin-bottom:8px;color:#3b465e}}
.bar-row{{display:grid;grid-template-columns:86px 1fr 46px;align-items:center;gap:8px;margin:6px 0}}
.bar-label{{font-size:10px;color:#5f6b84}} .bar{{height:8px;background:#eef2f8;border-radius:5px;overflow:hidden}}
.bar i{{display:block;height:100%;border-radius:5px}} .bar-row b{{font-size:10px;color:#3b465e;text-align:right}}
table{{width:100%;border-collapse:collapse;font-size:10.5px}}
th,td{{border:1px solid #dde4f0;padding:6px 8px;text-align:center}}
th{{background:#eef3fb;font-weight:700;color:#3b465e}} td.id{{font-weight:700;text-align:left}}
.yes{{color:#2e9e74;font-weight:700}} .no{{color:#cf5b6c;font-weight:700}}
.note{{font-size:9.5px;color:#7a8499;margin-top:10px;line-height:1.7}}
</style></head><body>
<h1>实验7 原型评测：基线与两个版本对比</h1>
<div class="sub">同一测试集（12 例：正常 4、信息不足 3、超出范围 2、边界 3）；模型 {meta['promptVersion']} / qwen-plus；同一检查规则；耗时包含网络往返</div>
<div class="cards">{''.join(cards)}</div>
<div class="charts">{bars('grounding', '引用可核验率')}{bars('coverage', '三类覆盖与信息不足处理')}</div>
<table><thead><tr><th>编号</th><th>类别</th><th>无 AI 基线</th><th>初版 v1</th><th>修订版 v2</th></tr></thead>
<tbody>{''.join(table_rows)}</tbody></table>
<div class="note">✓ 表示结构、引用、GWT 与覆盖四项程序检查同时通过；基线没有 requirementKind 字段，不计入类型判定。费用按输入 0.0008 元/千 Token、输出 0.002 元/千 Token 估算。人工判断见报告表 3-12。</div>
</body></html>"""


def write_comparison() -> None:
    datasets = {label: load(label) for label, _, _ in LABELS}
    if any(v is None for v in datasets.values()):
        return
    lines = ["# 三种方案对比", ""]
    lines.append("| 指标 | 无AI基线 | 初版 v1 | 修订版 v2 |")
    lines.append("|---|---|---|---|")
    keys = [("program", "程序可接受率"), ("schema", "结构合法率"), ("grounding", "引用可核验率"),
            ("coverage", "覆盖/范围处理率"), ("kind", "类型判定准确率"),
            ("latency", "平均耗时(ms)"), ("tokens", "总Token"), ("cost", "估算费用(元)")]
    rows = {label: metric_rows(data) for label, data in datasets.items()}
    for key, name in keys:
        lines.append(f"| {name} | {rows['rule'][key]} | {rows['v1'][key]} | {rows['v2'][key]} |")
    (EXP7 / "results" / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    (FIG / "数据流图.html").write_text(flow_html(), encoding="utf-8")
    (FIG / "评测看板.html").write_text(dashboard_html(), encoding="utf-8")
    write_comparison()
    print("figures written")