# 实验7：验收标准与测试样例生成原型

本目录是实验7“个人软件核心AI能力原型设计与开发”的原型配套文件，原型已集成进 AI 需求歧义审查器：
输入一段软件需求，调用千问 `qwen-plus` 生成带原文引用的验收标准（Given / When / Then）与正常、边界、异常三类测试样例；
信息不足或超出软件需求范围时，返回待确认问题或明确拒绝，而不是编造。

## 目录

| 路径 | 说明 |
|---|---|
| `testset.json` | 统一编号的 12 个评测样例（正常 4、信息不足 3、超范围 2、边界 3） |
| `run_eval.py` | 评测脚本：同一测试集分别运行 无AI基线 / 初版 / 修订版，记录输出、检查结果、耗时、Token 与估算费用 |
| `judgments.json` | 人工判断（usable + 说明），由评测脚本合并 |
| `results/<label>/` | 每次评测的 `results.json`、`summary.md` 与逐样例原始输出 |
| `smoke.py` | 单样例联调脚本 |
| `dashboard.html` | 评测结果对比看板（报告截图来源） |

## 启动

```powershell
# 后端（读取 backend/.env.local，端口 8080）
cd backend
.\run-local.ps1

# 前端（端口 5173）
cd frontend
npm run dev
```

打开 http://localhost:5173，左侧「验收标准」。

## 接口

```http
POST /api/acceptance/runs
{"text":"需求原文","promptVersion":"revised","mode":"model"}
```

- `mode=model`：调用模型；`mode=rule`：无AI模板基线。
- `promptVersion=original`：初版 Prompt；`revised`：修订版 Prompt（v2 起同时启用程序校验与修复循环）。
- 返回：`runId`、`status`、`promptVersion`、`model`、`durationMs`、`usage`、`report`、`checks`（v2）、`attempts`（v2）、`error`。
- 运行日志：`backend/logs/acceptance-runs/<runId>.jsonl`（逐事件）与 `<runId>.json`（完整产物，含原始输出与检查结果）。

## 评测

```powershell
cd experiments/exp7
python run_eval.py --label rule --mode rule --version revised
python run_eval.py --label v1 --mode model --version original
python run_eval.py --label v2 --mode model --version revised
```

三个标签使用同一份 `testset.json` 与同一套检查规则；`judgments.json` 中的 `label → 样例编号 → usable/note` 会被合并进结果与汇总。

## 版本

- v1（tag `exp7-v1`）：可运行初版，单次模型调用，无程序校验。
- v2（tag `exp7-v2`）：修订版，增加需求类型判定、引用核验、GWT/覆盖检查、校验失败修复循环与页面检查面板。