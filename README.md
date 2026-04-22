# XBTI Maker

Python 前后端一体的 XBTI 测试设计工作台 MVP。

## 本地运行

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开:

```text
http://127.0.0.1:8000
```

## 测试

```powershell
python -m pytest
```

## 当前 MVP 能力

- 新建项目并生成一份主题化测试草稿
- 以 JSON 形式编辑完整 `TestConfig`
- 运行配置校验
- 在浏览器中预览答题和评分结果
- 导出可独立运行的单文件 HTML

## Ark 流式生成

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

当前项目直接读取系统环境变量，至少需要配置：

```text
ARK_API_KEY
```

可选：

```text
ARK_BASE_URL
ARK_RESPONSES_PATH
ARK_MODEL_ID
ARK_REASONING_EFFORT
```

新建页会优先走流式生成接口 `/api/generation/stream`：

- `provider=ark`：调用 Ark Responses API
- `provider=local`：本地模拟流，便于无 key 联调前端

前端会把流式事件拆成两个区域：

- `reasoning`：展示模型思考流
- `output`：展示结构化 JSON 输出流
