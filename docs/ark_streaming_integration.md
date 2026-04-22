# Ark 流式生成接入说明

日期: 2026-04-21  
分支: `feature/ark-streaming-generation`

## 当前目标

在 XBTI Maker 中接入 Ark 平台 `doubao-seed-1-6-251015`，使用 Responses API 的流式返回能力，前端分开展示：

- 模型思考流
- 正式结构化输出流

## 环境变量

见 [`.env.example`](C:/Users/Trivedi/projects/xbti-maker/.env.example)。

最少需要：

```text
ARK_API_KEY
```

默认值：

```text
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_RESPONSES_PATH=/responses
ARK_MODEL_ID=doubao-seed-1-6-251015
ARK_REASONING_EFFORT=high
```

## 后端结构

- [app/services/ark_generation.py](C:/Users/Trivedi/projects/xbti-maker/app/services/ark_generation.py):1
  - 构建 Ark Responses 请求
  - 解析 SSE
  - 识别 `response.reasoning_summary_text.delta`
  - 识别 `response.output_text.delta`
  - 收集最终 JSON 并解析为 `TestConfig`

- [app/services/generation_service.py](C:/Users/Trivedi/projects/xbti-maker/app/services/generation_service.py):1
  - provider 编排层
  - 支持 `ark` / `local`

- [app/api/routes.py](C:/Users/Trivedi/projects/xbti-maker/app/api/routes.py):1
  - `POST /api/generation/stream`
  - 将 Ark 或本地 provider 的事件标准化成前端可消费的 SSE：
    - `status`
    - `reasoning`
    - `output`
    - `project_created`
    - `error`
    - `done`

## 前端结构

- [app/templates/projects/new.html](C:/Users/Trivedi/projects/xbti-maker/app/templates/projects/new.html):1
  - 新建页升级为流式生成工作台

- [app/static/js/generation_stream.js](C:/Users/Trivedi/projects/xbti-maker/app/static/js/generation_stream.js):1
  - 使用 `fetch` 读取 `text/event-stream`
  - 把思考和输出分栏渲染

- [app/static/css/app.css](C:/Users/Trivedi/projects/xbti-maker/app/static/css/app.css):1
  - 新增流式面板布局样式

## Prompt 策略

### Developer Prompt

约束模型：

- 输出必须是合法 JSON
- 严格遵循 `TestConfig` schema
- 不复制 MBTI / SBTI 现成题目和人格
- 结果文案需要有传播感，但不能只做羞辱式输出
- 保持娱乐定位，不做诊断

### User Prompt

来自 `ThemeBrief`：

- 主题
- 目标人群
- 语气
- 平台
- 题目数
- 维度数
- 结果数
- 是否要求隐藏人格

### 输出格式

Ark 请求里使用：

```json
"text": {
  "format": {
    "type": "json_schema",
    "name": "xbti_test_config",
    "schema": { ... },
    "strict": true
  }
}
```

## 当前验证状态

已验证：

- `local` provider 的流式接口可用
- 前后端 SSE 事件序列通了
- 单元测试通过

待你提供 key 后再做：

- 真机调 Ark SSE 事件字段
- 调整 prompt 细节和输出稳定性
- 对异常响应和超时做更细的 UX 优化
