# 实验8 集成与端到端测试材料

本目录保存实验8 的脚本、配置与测试结果。报告正文在 `实验文档/TEST8/`，截图在 `实验文档/TEST8/截图/`。

## 目录

| 文件 | 用途 |
| --- | --- |
| `smoke.mjs` | 主链路冒烟：创建档案 → 提交任务 → 轮询 → 编辑 → 保存 → 读取档案验收标准 |
| `e2e-normal.mjs` | 11 个端到端用例（正常/重复/取消/刷新/非法输入/信息不足/超范围/交错/编辑/放弃/转人工） |
| `e2e-fault.mjs` | 故障与恢复用例：模型不可用、模型超时、重启后恢复（分阶段执行） |
| `lib/cdp.mjs` | 无依赖的 Chrome DevTools Protocol 驱动与截图工具 |
| `diagrams.mjs` | 生成集成顺序图与任务状态机 SVG |
| `shoot-figures.mjs` | 把 SVG 渲染为报告用 PNG |
| `results/e2e-normal.json` | 端到端运行结果（含前置条件、步骤、预期、实际、证据文件） |
| `results/e2e-fault.json` | 故障与恢复运行结果 |
| `results/fault-context.json` | 三个阶段之间传递的档案与任务编号 |

## 运行

```powershell
# 后端（读取 backend/.env.local）与前端
cd backend; .\run-local.ps1
cd frontend; npm run build; npm run preview -- --host 127.0.0.1 --port 5173

node experiments/exp8/smoke.mjs
node experiments/exp8/e2e-normal.mjs

# 故障三阶段：每次重启后端为对应配置
node experiments/exp8/e2e-fault.mjs unavailable   # AI_MODE=qwen 且无 Key
node experiments/exp8/e2e-fault.mjs timeout        # ACCEPTANCE_TIMEOUT_MS=1 且有 Key
node experiments/exp8/e2e-fault.mjs restart        # 恢复正常配置重启后
```

## 固定配置

| 项 | 值 |
| --- | --- |
| 软件版本 | 见报告 3.5 的 Commit |
| 模型 | qwen-plus（OpenAI 兼容 chat/completions） |
| temperature / max-tokens | 0.2 / 2000 |
| 单次读超时 / 最大尝试 | 60000 ms / 3 |
| 任务线程池 | core 2，max 4，队列 20 |
| 任务保留期 | 30 天 |
| 前端 | Vite 构建产物，`vite preview` 于 127.0.0.1:5173 |
| 浏览器 | Chrome 无头模式 1500×1100 |

## 说明

- 端到端用例真实调用 qwen-plus，每次生成约 20–40 秒；用例中的耗时、Token、检查结果均来自实际响应。
- 故障用例不使用“假装失败”的开关：模型不可用通过不配置 Key 触发，超时通过把读超时设为 1 ms 触发。
- `results/*.json` 由脚本直接写入，报告中的表格与数字来自这些文件。