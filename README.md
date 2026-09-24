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

1. 进入审查页，粘贴需求或选择 `.docx` / 文字型 `.pdf`。
2. 上传后等待文本解析完成，可编辑抽取出的内容。
3. 选择审查模式并点击“开始审查”。
4. 在结果页筛选问题类型，查看引用、缺失条件、待确认问题、验收标准和返工风险。
5. 使用追问输入框继续询问，或返回编辑需求后重新审查。
6. 在历史页查看和删除本地历史记录及版本。

## API 概览

- `POST /api/reviews`：审查文本，JSON `{ "text": "...", "mode": "全面审查" }`
- `POST /api/reviews/upload`：上传 `.docx` / `.pdf`，解析并返回文本
- `POST /api/reviews/{id}/follow-up`：追问，JSON `{ "question": "..." }`
- `GET /api/reviews`：历史列表
- `GET /api/reviews/{id}`：详情及版本
- `DELETE /api/reviews/{id}`：删除历史

## 验证

前端已验证 `npm run build` 和开发地址 `http://127.0.0.1:5173/` 返回 200。后端可运行 `mvn test` 或 `backend/run-local.ps1`；当前环境曾因 Maven Central 网络超时而未完成依赖下载。当前原型使用 H2 文件数据库，数据保存在后端运行目录的 `data/` 下。

## 当前限制

- PDF 仅保证文字型 PDF，扫描件需要 OCR 扩展。
- Mock 报告用于演示流程，不替代真实模型判断。
- 未实现登录、多用户隔离、协作、支付和 MCP。
- 生产环境应增加文件大小/内容安全扫描、鉴权、限流和更严格的模型输出校验。
