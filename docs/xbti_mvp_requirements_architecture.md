# XBTI Maker MVP 需求分析与 Python 一体化架构设计

版本: 0.1  
日期: 2026-04-20  
范围: MVP 版本  
架构方向: Python 前后端一体单体应用

## 1. MVP 定位

XBTI Maker MVP 的目标不是一次性做成完整 SaaS，而是先打通一条最小但完整的生产链路:

```text
输入主题 -> AI 生成测试草稿 -> 人工编辑 -> 算法预览 -> 演示页面 -> 导出单文件 HTML
```

MVP 要证明三件事:

- 用户能用一个主题快速生成一套像样的 XBTI 测试。
- 生成结果不是散文，而是结构化、可编辑、可评分、可预览的数据。
- 最终产物能导出为独立 HTML，离开工作台也能运行。

因此，MVP 的核心不是「华丽的在线搭建器」，而是「结构化测试生产和导出闭环」。

## 2. MVP 目标

### 2.1 产品目标

- 支持用户新建一个 XBTI 项目。
- 支持输入主题、目标人群、语气风格，一键生成完整测试草稿。
- 支持编辑测试基础信息、维度、题目、结果人格、评分配置。
- 支持用默认 L/M/H 模板匹配算法计算结果。
- 支持在工作台内完成一次答题预览。
- 支持查看评分过程和命中结果。
- 支持导出一个可独立运行的 `index.html`。

### 2.2 技术目标

- 采用 Python 单体架构，降低早期研发和部署复杂度。
- 前后端一体，服务端渲染页面，少量 JS 增强交互。
- 业务逻辑与页面渲染分离，保证后续可平滑拆分 API 或前后端分离。
- 测试配置以 JSON Schema / Pydantic Model 为核心，便于 AI 生成、编辑、校验和导出。
- 评分引擎、AI 生成器、HTML 导出器独立成模块，避免写死在页面逻辑里。

### 2.3 不做目标

- 不做多人团队协作。
- 不做用户登录与复杂权限，MVP 可先本地单用户或简单账号。
- 不做真实答题数据统计看板。
- 不做模板市场。
- 不做自动部署。
- 不做复杂拖拽页面编辑器。
- 不做 A/B 测试。
- 不做多语言。

## 3. MVP 用户角色

### 3.1 创作者

主要用户。负责创建主题、生成测试、修改内容、预览、导出。

### 3.2 测试参与者

通过导出的 HTML 页面答题。MVP 中测试参与者不需要账号，答题数据默认只保存在浏览器本地，不回传服务器。

### 3.3 开发/运营人员

拿到导出的 HTML 后，可以上传到静态站、对象存储、活动页面或本地演示。

## 4. MVP 核心用户流程

### 4.1 新建并生成

1. 用户进入项目列表。
2. 点击「新建测试」。
3. 填写主题 Brief:
   - 测试主题
   - 目标人群
   - 语气风格
   - 题目数量
   - 结果数量
   - 是否允许隐藏人格
4. 点击「AI 生成草稿」。
5. 系统生成:
   - 测试基础信息
   - 维度模型
   - 题库
   - 结果人格
   - 评分配置
   - 基础页面主题
6. 用户进入编辑工作台。

### 4.2 编辑与校验

1. 用户在概览页查看完整度。
2. 用户编辑维度定义。
3. 用户编辑题目和选项分值。
4. 用户编辑结果人格文案。
5. 用户运行质量检查。
6. 系统提示:
   - 未绑定维度的题
   - 没有题目的维度
   - 不可达结果
   - 题目数量不足
   - 结果数量不足
   - 模板向量长度不一致

### 4.3 预览与评分调试

1. 用户点击「预览答题」。
2. 系统以测试参与者视角展示答题页。
3. 用户完成答题后进入结果页。
4. 系统展示:
   - 最终人格
   - 匹配度
   - 维度得分
   - L/M/H 向量
   - Top 5 候选结果
   - 触发规则

### 4.4 导出 HTML

1. 用户点击「导出」。
2. 系统运行导出前检查。
3. 检查通过后生成单文件 HTML。
4. 用户可下载或在本地打开导出的 HTML。
5. HTML 中内嵌:
   - 测试配置 JSON
   - CSS
   - JS 评分运行时
   - 页面模板

## 5. MVP 功能范围

## 5.1 项目管理

### 功能

- 项目列表
- 新建项目
- 编辑项目名称、主题、描述
- 删除项目
- 复制项目
- 查看最近更新时间

### 字段

- 项目 ID
- 名称
- 主题
- 状态: 草稿、可预览、可导出
- 创建时间
- 更新时间

### MVP 简化

- 不做团队空间。
- 不做复杂权限。
- 不做云端发布状态。

## 5.2 主题 Brief 与 AI 生成

### 功能

- 用户填写主题 Brief。
- 系统调用 AI 生成完整测试配置。
- 生成失败时展示错误并允许重试。
- 生成结果保存为项目当前版本。

### Brief 字段

- `topic`: 测试主题
- `audience`: 目标用户
- `tone`: 语气风格
- `platform`: 传播平台，可选
- `question_count`: 题目数量，默认 30
- `dimension_count`: 维度数量，默认 15
- `result_count`: 结果数量，默认 24
- `allow_hidden_results`: 是否允许隐藏人格
- `safety_level`: 内容安全级别，默认普通

### AI 生成内容

- 测试名称
- 测试说明
- 免责声明
- 维度组
- 维度
- 题目
- 结果人格
- 评分配置
- 页面主题

### MVP 生成策略

MVP 阶段不追求复杂多轮 agent，而采用「单次结构化生成 + 校验失败局部重试」:

1. 服务端拼接系统提示词和用户 Brief。
2. 要求 AI 返回符合 JSON Schema 的测试配置。
3. 使用 Pydantic 校验。
4. 如果结构不合法，要求 AI 修复 JSON。
5. 如果内容有缺失，系统用规则补齐或提示用户。

## 5.3 测试配置编辑

### 基础信息编辑

- 测试名称
- 副标题
- 介绍文案
- 免责声明
- 开始按钮文案
- 结果页默认分享文案

### 维度编辑

- 新增、删除、编辑维度组
- 新增、删除、编辑维度
- 编辑 L/M/H 描述
- 编辑权重
- 检查维度是否有题目覆盖

### 题库编辑

- 新增题目
- 删除题目
- 编辑题干
- 编辑题型，MVP 只支持单选
- 编辑所属维度
- 编辑选项文本
- 编辑选项分值
- 设置是否计分
- 设置是否 gate 题
- 设置展示条件，MVP 可先做简单条件

### 结果人格编辑

- 新增结果
- 删除结果
- 编辑人格代码
- 编辑中文名
- 编辑一句话
- 编辑长文
- 编辑模板向量
- 编辑是否隐藏
- 编辑优先级

### 评分配置编辑

- 评分算法，MVP 固定为 `level_distance`
- L/M/H 阈值
- 兜底结果
- 最低匹配度阈值
- 隐藏规则优先级

## 5.4 质量检查

### 检查项

- 测试名称不能为空。
- 至少有 3 个维度。
- 每个正式维度至少 1 道题，推荐 2 道。
- 每道正式题必须绑定维度。
- 每道正式题至少 2 个选项。
- 每个计分选项必须有分值。
- 每个结果人格必须有模板向量。
- 模板向量长度必须等于维度数量。
- 模板向量只能包含 L/M/H。
- 兜底结果必须存在。
- 隐藏规则引用的题目和选项必须存在。
- 至少有 2 个可命中的标准结果。

### 检查级别

- Error: 阻止导出。
- Warning: 可导出，但需要用户确认。
- Info: 优化建议。

## 5.5 答题预览

### 功能

- 在工作台中打开预览页。
- 展示开始页。
- 顺序或随机展示题目。
- 用户选择选项。
- 支持上一题。
- 完成后展示结果页。
- 展示评分调试信息。

### MVP 简化

- 暂不做复杂动画。
- 暂不生成分享图片。
- 暂不做真实数据上报。

## 5.6 HTML 导出

### 功能

- 导出单文件 HTML。
- HTML 本地打开可运行。
- HTML 内不依赖后端。
- 导出的页面包含开始页、答题页、结果页。
- 答题过程保存在浏览器内存或 localStorage。

### 单文件结构

```html
<!doctype html>
<html>
  <head>
    <style>/* exported css */</style>
  </head>
  <body>
    <div id="app"></div>
    <script type="application/json" id="xbti-config">{...}</script>
    <script>
      // exported runtime
    </script>
  </body>
</html>
```

### 导出前检查

- 运行质量检查。
- Error 为 0 才允许导出。
- Warning 展示确认。

## 6. MVP 评分算法

### 6.1 数据输入

- 维度列表
- 题目列表
- 用户答案
- 结果人格模板
- 评分配置
- 特殊规则

### 6.2 计算过程

1. 初始化每个维度总分为 0。
2. 遍历用户答案。
3. 找到题目绑定的维度。
4. 将选项分值累加到维度。
5. 根据阈值将维度分数映射为 L/M/H。
6. 检查隐藏规则是否触发。
7. 如果没有隐藏结果，则计算用户向量与每个标准人格模板的距离。
8. 按距离、精确命中数、优先级排序。
9. 计算匹配度。
10. 如果匹配度低于阈值，返回兜底人格。
11. 返回最终结果和调试信息。

### 6.3 默认阈值

如果每个维度有 2 道题，每题 1-3 分:

```text
维度总分范围: 2-6
2-3 => L
4   => M
5-6 => H
```

如果某维度题目数不是 2，使用归一化:

```text
normalized = (score - min_score) / (max_score - min_score)
0.00 - 0.40 => L
0.40 - 0.65 => M
0.65 - 1.00 => H
```

### 6.4 距离公式

```text
L = 0, M = 1, H = 2
distance = sum(weight[d] * abs(user_level[d] - template_level[d]))
max_distance = sum(weight[d] * 2)
similarity = round((1 - distance / max_distance) * 100)
```

### 6.5 排序规则

```text
1. distance 越小越优先
2. exact_matches 越多越优先
3. priority 越高越优先
4. result_id 字典序兜底，保证可复现
```

### 6.6 隐藏规则 MVP

MVP 只支持最简单的选项命中规则:

```text
IF answer[question_id] == option_id
THEN result = result_id
```

后续再扩展:

- 多条件 AND/OR
- 维度极值规则
- 组合选项规则
- 结果覆盖策略

## 7. 推荐技术选型

## 7.1 总体选择

推荐采用:

```text
FastAPI + Jinja2 + HTMX/Alpine.js + SQLite + SQLModel/Pydantic
```

### 为什么不是前后端分离

MVP 的核心风险在产品链路和结构化生成，不在复杂交互。前后端分离会增加:

- 两套路由
- 两套构建
- CORS/API 权限
- 状态同步复杂度
- 部署复杂度

Python 前后端一体更适合快速验证。

### 为什么选 FastAPI

- Pydantic 生态适合做结构化测试配置。
- API 和服务端页面可以共存。
- 后续拆出纯 API 较容易。
- 自动文档方便调试内部接口。
- Python AI SDK 接入自然。

### 为什么不用 Django 作为 MVP 首选

Django 适合后台 CRUD 和权限体系，但 MVP 的核心是 JSON 配置、AI 生成、导出运行时和算法服务。FastAPI 更轻，和 Pydantic 模型结合更顺。  
如果后续要做团队、多租户、权限、后台运营，Django 也可以作为增强路线。

### 为什么不用 Streamlit/Gradio

Streamlit/Gradio 适合内部工具原型，但不适合导出产品化 HTML、复杂页面流程和后续 SaaS 化。

## 7.2 前端策略

采用服务端渲染为主:

- Jinja2 渲染页面。
- HTMX 处理局部刷新，例如保存题目、增加选项、运行检查。
- Alpine.js 处理轻量本地状态，例如预览答题、折叠面板、tab。
- 原生 CSS 或 Tailwind CSS 构建基础样式。
- 不引入 React/Vue，除非后续页面编辑器复杂度明显上升。

## 7.3 数据库

MVP 推荐 SQLite:

- 本地开发简单。
- 单用户/小团队足够。
- 易备份。
- 后续可迁移 PostgreSQL。

ORM 推荐 SQLModel:

- 同时兼顾 SQLAlchemy 和 Pydantic。
- 适合 FastAPI。
- 类型定义集中。

## 7.4 AI 接入

AI 服务封装为 provider:

```text
app/services/ai/
  provider.py
  openai_provider.py
  prompts.py
  schemas.py
```

业务代码只调用:

```python
generate_test_config(brief: ThemeBrief) -> TestConfig
repair_test_config(raw: str, errors: list[str]) -> TestConfig
rewrite_text(text: str, tone: str) -> str
```

这样后续可替换模型或接入多模型。

## 8. 系统架构

### 8.1 逻辑架构

```text
Browser
  |
  | HTML form / HTMX / fetch
  v
FastAPI App
  |
  +-- Web Routes       服务端页面
  +-- API Routes       JSON 接口
  +-- Application      用例编排
  +-- Domain Services  评分、校验、导出、AI 生成
  +-- Repositories     数据访问
  +-- SQLite           项目、版本、导出记录
  +-- File Storage     导出的 HTML 文件
```

### 8.2 模块架构

```text
app/
  main.py
  core/
    config.py
    database.py
    errors.py
  models/
    project.py
    test_version.py
    export_bundle.py
  schemas/
    brief.py
    test_config.py
    scoring.py
    validation.py
  repositories/
    project_repo.py
    version_repo.py
    export_repo.py
  services/
    ai/
      provider.py
      openai_provider.py
      prompts.py
    generator_service.py
    validation_service.py
    scoring_service.py
    export_service.py
    preview_service.py
  web/
    routes.py
    project_routes.py
    editor_routes.py
    preview_routes.py
    export_routes.py
  api/
    routes.py
    project_api.py
    generation_api.py
    scoring_api.py
    export_api.py
  templates/
    base.html
    projects/
      index.html
      new.html
      detail.html
    editor/
      overview.html
      dimensions.html
      questions.html
      results.html
      scoring.html
    preview/
      preview.html
      result_debug.html
    exports/
      export.html
    exported/
      standalone.html
  static/
    css/
      app.css
    js/
      editor.js
      preview.js
      exported_runtime.js
  storage/
    exports/
```

### 8.3 分层职责

### Web Routes

负责:

- 接收浏览器请求。
- 调用 application/service。
- 返回 HTML 模板或局部 HTML。

不负责:

- 直接写评分算法。
- 直接拼 AI prompt。
- 直接处理复杂数据校验。

### API Routes

负责:

- 为预览、保存、导出等操作提供 JSON 接口。
- 后续给前后端分离预留迁移路径。

### Services

负责核心业务:

- AI 生成
- 配置校验
- 评分计算
- HTML 导出
- 预览数据组装

### Repositories

负责:

- 项目读写
- 版本读写
- 导出记录读写

### Schemas

负责:

- Pydantic 数据结构
- JSON Schema 生成
- 请求/响应格式
- AI 输出格式校验

## 9. 数据模型设计

## 9.1 数据库存储模型

MVP 重点避免把维度、题目、结果拆成大量关系表。因为 AI 生成和导出都围绕一份完整配置 JSON 工作。推荐采用「项目元数据关系化 + 测试配置 JSON 化」。

### `projects`

```text
id                string / uuid
name              string
topic             string
description       text
status            string
created_at        datetime
updated_at        datetime
```

### `test_versions`

```text
id                string / uuid
project_id        string / uuid
version_number    integer
config_json       json/text
is_current        boolean
created_at        datetime
updated_at        datetime
```

### `export_bundles`

```text
id                string / uuid
project_id        string / uuid
version_id        string / uuid
file_path         string
format            string
created_at        datetime
```

### `generation_jobs`

MVP 可选。若 AI 生成是同步请求，可以先不建表。若生成时间较长，建议记录:

```text
id                string / uuid
project_id        string / uuid
status            string
brief_json        json/text
error_message     text
created_at        datetime
updated_at        datetime
```

## 9.2 TestConfig Schema

`TestConfig` 是整个系统最重要的数据结构。

```text
TestConfig
  meta
  theme
  dimension_groups
  dimensions
  questions
  results
  rules
  scoring
  page
```

### `meta`

```json
{
  "schema_version": "1.0",
  "test_id": "coffee-xbti",
  "name": "咖啡人格 XBTI",
  "subtitle": "测测你是哪种咖啡精神体",
  "description": "一个仅供娱乐的趣味测试。",
  "disclaimer": "本测试仅供娱乐，不构成心理诊断或专业建议。"
}
```

### `dimension_groups`

```json
[
  {
    "id": "self",
    "name": "自我模型",
    "description": "你如何理解自己的状态。"
  }
]
```

### `dimensions`

```json
[
  {
    "id": "S1",
    "group_id": "self",
    "name": "自我能量",
    "description": "衡量用户的自我驱动强度。",
    "low_label": "更偏回血型",
    "mid_label": "看状态波动",
    "high_label": "持续高能推进",
    "weight": 1
  }
]
```

### `questions`

```json
[
  {
    "id": "q1",
    "text": "周一早上，你更像哪种状态？",
    "type": "single_choice",
    "dimension_id": "S1",
    "is_scored": true,
    "is_gate": false,
    "display_condition": null,
    "options": [
      { "id": "a", "text": "先别说话，让我重启一下", "score": 1 },
      { "id": "b", "text": "喝口水再决定做人方式", "score": 2 },
      { "id": "c", "text": "打开电脑，开始清扫世界", "score": 3 }
    ]
  }
]
```

### `results`

```json
[
  {
    "id": "CTRL",
    "code": "CTRL",
    "name": "拿捏者",
    "kind": "standard",
    "template": ["H", "M", "L"],
    "priority": 100,
    "headline": "你的人生像一张会自动排期的表格。",
    "description": "长文结果...",
    "share_text": "我测出了 CTRL，谁懂。"
  }
]
```

### `rules`

```json
[
  {
    "id": "hidden_drunk",
    "type": "answer_equals",
    "question_id": "q_gate_2",
    "option_id": "b",
    "result_id": "DRUNK",
    "priority": 1000
  }
]
```

### `scoring`

```json
{
  "algorithm": "level_distance",
  "level_mode": "normalized",
  "low_max": 0.4,
  "mid_max": 0.65,
  "fallback_result_id": "MIXED",
  "min_similarity": 60,
  "shuffle_questions": true
}
```

### `page`

```json
{
  "theme": "clean_fun",
  "primary_color": "#111111",
  "accent_color": "#2f9e44",
  "start_button_text": "开始测试",
  "result_button_text": "再测一次"
}
```

## 10. 路由与页面设计

## 10.1 Web 页面路由

```text
GET  /                         项目列表
GET  /projects/new             新建项目页
POST /projects                 创建项目
GET  /projects/{id}            项目概览
GET  /projects/{id}/brief      Brief 与生成页
POST /projects/{id}/generate   AI 生成草稿
GET  /projects/{id}/editor     编辑器概览
GET  /projects/{id}/dimensions 维度编辑
GET  /projects/{id}/questions  题库编辑
GET  /projects/{id}/results    结果编辑
GET  /projects/{id}/scoring    评分配置
GET  /projects/{id}/preview    预览答题
GET  /projects/{id}/export     导出页
POST /projects/{id}/export     创建导出
GET  /exports/{export_id}      下载导出文件
```

## 10.2 JSON API 路由

```text
GET  /api/projects/{id}/config
PUT  /api/projects/{id}/config
POST /api/projects/{id}/validate
POST /api/projects/{id}/score
POST /api/projects/{id}/simulate
POST /api/projects/{id}/export
```

MVP 中 Web Routes 和 API Routes 可以共存。页面表单走 Web Routes，复杂交互走 API。

## 11. 页面 MVP 设计

## 11.1 项目列表页

展示:

- 项目名称
- 主题
- 状态
- 更新时间
- 操作: 继续编辑、预览、导出、复制、删除

## 11.2 新建项目页

表单:

- 项目名称
- 主题
- 目标人群
- 语气风格
- 题目数量
- 结果数量

按钮:

- 创建空白项目
- 创建并 AI 生成

## 11.3 工作台概览页

展示:

- 测试名称
- 当前版本
- 维度数
- 题目数
- 结果数
- 检查结果
- 最近导出

快捷操作:

- 继续生成
- 编辑题库
- 预览
- 导出

## 11.4 维度编辑页

采用表格编辑:

- 维度 ID
- 分组
- 名称
- L 描述
- M 描述
- H 描述
- 权重
- 覆盖题数

## 11.5 题库编辑页

MVP 可采用「列表 + 详情表单」:

- 左侧题目列表。
- 右侧题目编辑。
- 选项可增删。
- 保存后局部刷新。

## 11.6 结果编辑页

字段:

- 代码
- 名称
- 类型
- 模板向量
- 一句话
- 长文
- 分享文案

提供辅助:

- 模板向量长度检查
- L/M/H 输入提示

## 11.7 评分配置页

展示:

- 算法说明
- 阈值配置
- 兜底结果选择
- 隐藏规则列表
- 测试答案 JSON 输入框，可用于调试

## 11.8 预览页

预览页应尽量接近导出 HTML 的运行效果，但可以额外展示调试信息。

包含:

- 开始页
- 答题页
- 结果页
- 调试面板

## 11.9 导出页

展示:

- 导出前检查
- 导出按钮
- 最近导出记录
- 下载链接

## 12. AI 生成架构

## 12.1 Prompt 分层

### System Prompt

定义角色和安全边界:

- 你是趣味人格测试产品策划。
- 输出必须是结构化 JSON。
- 内容仅供娱乐，不做心理诊断。
- 不复制现有 SBTI 文案。
- 避免歧视、仇恨、医疗建议、自残鼓励。

### Developer Prompt

定义结构:

- 必须生成 N 个维度。
- 必须生成 N 道题。
- 每道题必须绑定维度。
- 每个维度至少 1 道题。
- 每个结果必须有模板向量。
- 模板向量长度等于维度数。

### User Prompt

来自 Brief:

- 主题
- 目标人群
- 语气
- 平台
- 规模
- 边界要求

## 12.2 生成后处理

AI 返回后:

1. 清理 markdown 包裹。
2. 解析 JSON。
3. Pydantic 校验。
4. 运行业务质量检查。
5. 自动补充缺省字段。
6. 保存当前版本。

## 12.3 错误处理

常见错误:

- JSON 无法解析
- 缺少字段
- ID 重复
- 模板长度不一致
- 题目未绑定维度

处理策略:

- 结构错误: 调用 repair prompt。
- 业务错误: 尝试本地规则修复。
- 无法修复: 展示错误给用户，并保留原始输出供调试。

## 13. HTML 导出架构

## 13.1 导出输入

- `TestConfig`
- 导出模板 `templates/exported/standalone.html`
- 导出运行时 `static/js/exported_runtime.js`
- 导出样式 `static/css/exported.css`

## 13.2 导出流程

```text
load current config
  -> validate config
  -> serialize config json
  -> load css
  -> load runtime js
  -> render standalone.html
  -> write storage/exports/{project_id}/{timestamp}/index.html
  -> save export record
  -> return download link
```

## 13.3 导出运行时职责

导出 HTML 内的 JS runtime 负责:

- 读取 `xbti-config`
- 渲染开始页
- 渲染题目
- 处理选项点击
- 控制题目进度
- 计算分数
- 匹配结果
- 渲染结果页
- 重新测试

导出 runtime 不能依赖服务端 API。

## 14. 文件与目录建议

MVP 项目目录:

```text
xbti-maker/
  pyproject.toml
  README.md
  .env.example
  app/
    main.py
    core/
    models/
    schemas/
    repositories/
    services/
    web/
    api/
    templates/
    static/
  migrations/
  tests/
    unit/
      test_scoring_service.py
      test_validation_service.py
      test_export_service.py
    fixtures/
      sample_config.json
  storage/
    exports/
  docs/
    xbti_product_design.md
    xbti_mvp_requirements_architecture.md
```

## 15. 核心服务设计

## 15.1 `ScoringService`

接口:

```python
class ScoringService:
    def score(self, config: TestConfig, answers: dict[str, str]) -> ScoreResult:
        ...
```

返回:

```text
ScoreResult
  result_id
  similarity
  dimension_scores
  dimension_levels
  user_vector
  candidates
  triggered_rules
```

## 15.2 `ValidationService`

接口:

```python
class ValidationService:
    def validate_config(self, config: TestConfig) -> ValidationReport:
        ...
```

返回:

```text
ValidationReport
  errors
  warnings
  infos
```

## 15.3 `GenerationService`

接口:

```python
class GenerationService:
    def generate_from_brief(self, brief: ThemeBrief) -> TestConfig:
        ...
```

职责:

- 拼 prompt
- 调 AI provider
- 校验输出
- 修复输出
- 返回 TestConfig

## 15.4 `ExportService`

接口:

```python
class ExportService:
    def export_html(self, project_id: str, config: TestConfig) -> ExportBundle:
        ...
```

职责:

- 导出前检查
- 读取导出模板
- 内嵌配置、CSS、JS
- 写文件
- 保存记录

## 15.5 `ProjectService`

职责:

- 创建项目
- 获取当前版本
- 保存配置
- 复制项目
- 删除项目

## 16. 测试策略

MVP 最需要测试的不是页面，而是核心确定性逻辑。

### 必测

- 评分算法
- L/M/H 阈值映射
- 距离排序
- 兜底结果
- 隐藏规则触发
- 配置校验
- HTML 导出包含必要内容

### 建议测试文件

```text
tests/unit/test_scoring_service.py
tests/unit/test_validation_service.py
tests/unit/test_export_service.py
tests/fixtures/sample_config.json
```

### 关键用例

- 完全命中某人格模板。
- 两个人格距离相同，按 exact_matches 排序。
- 相似度低于阈值，返回兜底人格。
- 隐藏规则命中，覆盖标准人格。
- 模板向量长度不一致，校验报错。
- 导出 HTML 中包含配置 JSON 和运行时脚本。

## 17. 开发里程碑

### Milestone 1: 项目骨架与数据模型

- FastAPI 项目初始化
- SQLite/SQLModel 配置
- Project/TestVersion/ExportBundle 模型
- TestConfig Pydantic Schema
- 项目列表和新建页

验收:

- 可创建项目。
- 可保存一份静态 sample config。

### Milestone 2: 评分与校验核心

- ScoringService
- ValidationService
- 单元测试
- 评分调试 API

验收:

- 使用 sample config 可以提交答案并得到结果。
- 错误配置可以被检查出来。

### Milestone 3: 编辑器 MVP

- 基础信息编辑
- 维度编辑
- 题库编辑
- 结果编辑
- 评分配置编辑

验收:

- 用户可以从页面修改并保存完整 config。

### Milestone 4: 预览运行

- 工作台预览页
- 答题流程
- 结果页
- 调试面板

验收:

- 用户可以在工作台完成一次答题并看到结果。

### Milestone 5: AI 生成

- ThemeBrief 表单
- AI Provider
- 结构化生成
- Pydantic 校验和错误修复

验收:

- 输入主题后可生成完整可编辑测试。

### Milestone 6: HTML 导出

- Standalone 模板
- Exported runtime
- 导出服务
- 下载导出文件

验收:

- 导出的 HTML 本地打开可完整答题并展示结果。

## 18. MVP 验收标准

### 功能验收

- 能创建项目。
- 能通过 AI 生成完整测试。
- 能人工编辑维度、题目、结果。
- 能运行质量检查。
- 能完成答题预览。
- 能看到评分调试信息。
- 能导出独立 HTML。
- 导出 HTML 无后端依赖。

### 内容验收

- 生成的题目都绑定维度。
- 每个结果都有模板向量。
- 结果文案符合娱乐测试定位。
- 默认包含免责声明。

### 技术验收

- 核心服务有单元测试。
- 配置 JSON 可被 Pydantic 校验。
- 导出 HTML 可复现评分结果。
- 本地开发启动步骤清晰。

## 19. 后续演进

### 从单体到模块化单体

MVP 完成后，继续保持单体，但强化模块边界:

- AI 生成服务独立。
- 导出服务独立。
- 评分引擎可作为纯 Python 包复用。

### 从服务端渲染到前后端分离

当出现以下信号时，再考虑 React/Vue:

- 题库编辑需要大量拖拽和复杂状态。
- 页面搭建器需要实时设计画布。
- 多人协作需要复杂客户端状态同步。
- 移动端编辑体验成为核心需求。

### 从 SQLite 到 PostgreSQL

当出现以下信号时迁移:

- 多用户并发编辑。
- 项目数和版本数快速增长。
- 需要更复杂查询。
- 需要部署到生产 SaaS。

### 从单文件导出到发布平台

后续可以增加:

- 静态资源包导出
- 一键部署
- 短链
- 数据回流
- 分享卡生成
- 品牌白标

## 20. 推荐 MVP 决策

最终建议:

- Web 框架: FastAPI
- 页面渲染: Jinja2
- 轻交互: HTMX + Alpine.js
- 数据库: SQLite
- ORM: SQLModel
- 数据校验: Pydantic
- AI 接入: Provider 抽象，先接一个模型
- 核心配置: TestConfig JSON
- 导出格式: 单文件 HTML
- 第一优先级: 评分、校验、导出闭环

这套架构的优势是足够轻，能尽快把产品从「设计文档」推到「可演示工具」。同时，评分引擎、AI 生成、导出器都被明确隔离，后续无论是做 SaaS、拆 API、换前端，还是接入更复杂的算法，都不会推倒重来。
