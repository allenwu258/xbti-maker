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
