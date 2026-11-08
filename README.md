# AI 需求歧义审查器

面向课程作业的需求质量审查原型：粘贴需求或上传 Word/PDF，生成带原文引用、风险等级、待确认问题和可测试验收标准的结构化报告。

## 项目结构

- `frontend/`：Vue 3 + Vite + TypeScript + Element Plus 前端
- `backend/`：Spring Boot 3 + Java 17 REST 后端，负责文档解析、AI 调用和 H2 历史记录

## 环境要求

- Node.js 20+（Node 18+ 通常也可运行）
- Java 17+
- Maven 3.9+，或使用 `backend/run-local.ps1` 自动寻找本机 Maven

## 启动

### 一键启动（Windows）

在项目根目录双击 `启动项目.bat`。它会自动启动后端和前端，等待前端就绪后打开浏览器。

- 后端窗口：Spring Boot，端口 8080
- 前端窗口：Vite，端口 5173
- 关闭服务：运行根目录的 `停止项目.ps1`
- 如果端口已经有服务运行，启动器会复用现有服务，不会重复启动。

### 后端

```powershell
cd backend
# Windows：自动寻找 PATH 或 Maven 缓存中的 Maven
.\run-local.ps1
# 或使用本机 Maven
mvn spring-boot:run
```

默认监听 `http://localhost:8080`，API 前缀为 `/api`。首次构建需要访问 Maven Central 下载依赖；如果网络受限，请配置 Maven 镜像后重试。

### 前端

```powershell
cd frontend
npm install
npm run dev
```

默认打开 `http://localhost:5173`。可通过 `frontend/.env` 设置 `VITE_API_BASE_URL=http://localhost:8080/api`。

## 千问配置与 Mock 模式

复制 `backend/.env.example` 中的配置到运行环境，或在启动前设置环境变量：

```powershell
$env:AI_MODE="mock"
$env:DASHSCOPE_API_KEY=""
```

默认即为 Mock 模式，不需要 API Key，适合演示完整流程。接入千问时：

```powershell
$env:AI_MODE="qwen"
$env:DASHSCOPE_API_KEY="你的千问APIKey"
$env:QWEN_MODEL="qwen-plus"
```

API Key 只在后端使用，不会传给浏览器。千问返回内容要求为固定 JSON，后端会清理 markdown 代码围栏、校验字段并在异常时返回可理解错误。

## 使用流程

1. 进入审查页，粘贴需求或选择 `.docx` / `.pdf`。
2. 上传后等待正文解析及图片识别完成。界面仅显示文件卡片、字数和识别范围，正文在后台参与审查；点击“清空”可切回粘贴文字。
3. 选择审查模式并点击“开始审查”。
4. 在结果页筛选问题类型，查看引用、缺失条件、待确认问题、验收标准和返工风险。
5. 使用追问输入框继续询问，或返回编辑需求后重新审查。
6. 在审查结果页点击“导出 PDF”，或在审查档案行点击下载图标，下载该档案当前版本的完整报告；历史记录仍可查看、追问和删除。

## API 概览

- `POST /api/reviews`：审查文本，JSON `{ "text": "...", "mode": "全面审查", "promptVersion": "revised" }`；`promptVersion` 可选 `original` 或 `revised`，用于同一问题的 Prompt 对比实验。
- `POST /api/reviews/upload`：上传 `.docx` / `.pdf`，解析并返回正文、图像识别结果、文件信息和未识别范围
- `POST /api/reviews/{id}/follow-up`：追问，JSON `{ "question": "..." }`
- `POST /api/agent/runs`：档案分析 Agent，JSON `{ "question": "..." }`；返回 `taskId`、`status`、`answer`、`steps[]`
- `POST /api/agent/runs/{taskId}/confirm`：确认或拒绝写操作，JSON `{ "approved": true }`
- `GET /api/reviews`：历史列表
- `GET /api/reviews/{id}`：详情及版本
- `DELETE /api/reviews/{id}`：删除历史

## 档案分析 Agent（实验6）

侧边栏「档案分析」用自然语言查询审查档案。Agent 只能调用 5 个白名单工具：
`list_reviews`、`compute_risk_stats`、`get_review_detail`、`search_knowledge`（只读）和
`delete_review`（写操作，必须人工确认）。工具名、参数 Schema、最大步数、模型/工具超时、
总时限和回答中的统计数字校验全部由程序执行；每次运行写入
`backend/logs/agent-runs/<taskId>.jsonl`。运行与配置细节见 `实验文档/TEST6/运行说明.md`。

## 验证

前端执行 `npm run build`，包含 `vue-tsc -b` TypeScript 检查。后端执行 `mvn test`，涵盖 REST 档案流程和 PDF 报告导出。当前原型使用 H2 文件数据库，数据保存在后端运行目录的 `data/` 下。

## 当前限制

- 文档最大 10 MB，正文与图片识别转录合计不超过 20000 个字符；超过时明确拒绝，不截断。
- Word 支持正文、表格、页眉页脚和可解码的内嵌位图；原生形状、SmartArt、图表及 EMF/WMF/SVG 等对象建议先导出 PDF 再上传。
- PDF 逐页渲染后交给视觉模型，可覆盖扫描页、矢量 UML、流程图和内嵌图片。默认最多识别前 30 页或前 30 张 Word 图片，超过部分会明确提示。
- 视觉模型可能误读低清晰度图片、复杂关系和箭头方向，需要核对原图；未识别范围会保留在页面、档案和导出的报告中。
- 原始 Word/PDF 二进制文件不会作为附件永久存入档案，档案保存来源文件名、正文、图像转录和识别提示。
- Mock 报告用于演示流程，不替代真实模型判断。
- 未实现登录、多用户隔离、协作、支付和 MCP。
- 生产环境应增加文件大小/内容安全扫描、鉴权、限流和更严格的模型输出校验。

## 图片 / UML 识别配置

`backend/run-local.ps1` 会读取 `backend/.env.local`。现有文本模型配置继续有效，新增视觉通道默认使用 `qwen-vl-max`：

```dotenv
AI_MODE=qwen
DASHSCOPE_API_KEY=你的千问APIKey
QWEN_MODEL=qwen-plus
VISION_ENABLED=true
QWEN_VISION_MODEL=qwen-vl-max
VISION_MAX_UNITS=30
```

修改后重启后端。账号必须有指定视觉模型的调用权限和可用额度；若使用国际站或自建网关，请配置相匹配的 `QWEN_VISION_URL` 和模型名称。视觉接口地址默认复用 `QWEN_URL`。Word 图片或 PDF 页面的渲染图会发送到该视觉接口，识别需要额外时间并产生相应模型费用。Mock 模式不会调用视觉接口，也不会伪造图片识别结果。未配置视觉通道或识别失败时，含正文的文档仍可审查，但会明确提示遗漏范围；纯扫描件或纯图片文档无法识别时拒绝审查。旧版 `.doc` 请先另存为 `.docx`。

## PDF 中文字体与接口

Windows 自动寻找系统黑体或仿宋字体，无需额外配置。部署到其他机器若找不到中文字体，请设置 `PDF_FONT_PATH` 为支持中文、可嵌入的 TTF 字体文件的绝对路径，然后重启后端。字体由 PDFBox 嵌入报告，阅读端不需要安装该字体。报告导出不调用模型。

`GET /api/reviews/{id}/report.pdf` 下载当前完整报告，包含全部发现项、证据、验收标准、检索来源、审查输入和文档识别范围，不受页面筛选影响。

## 新功能验证

- `frontend/`：`npm run build`，包含 TypeScript 检查。
- `backend/`：`mvn test`，覆盖 Word 表格和图片、扫描 PDF、视觉不可用 / 失败 / 数量限制、长文档拒绝、中文多页 PDF，以及档案保存、追问和 PDF 下载接口。测试使用临时内存数据库，不修改本地历史档案。PDF 测试需要本机可用的中文 TTF 字体；生成的视觉检查样例位于 `backend/target/test-artifacts/report.pdf`。

