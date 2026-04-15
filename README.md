# JD Smart CS Agent - 京东智能客服系统

基于 LangGraph 和 FastAPI 构建的智能客服 Agent 框架，支持多轮对话、FAQ 知识库检索、意图识别和风控机制。

## 🎯 项目概述

本项目是一个智能客服解决方案，旨在通过 AI Agent 为用户提供专业、准确的客服服务。系统具备以下核心能力：

- **多轮对话记忆**：支持上下文理解，记住用户历史对话（默认保留最近 20 轮）
- **FAQ 知识库检索**：从知识库中快速获取准确的客服信息
- **意图识别**：自动识别用户意图（订单查询、退款、物流、支付等）
- **风控机制**：识别异常查询和恶意请求，确保服务安全
- **流式输出**：支持实时流式响应，提升用户体验

## 🏗️ 项目结构

```
JD-Smart-CS-Agent/
├── src/
│   ├── agents/
│   │   └── agent.py              # 智能客服 Agent 主逻辑
│   ├── graphs/                    # 工作流图（可选功能模块）
│   │   ├── graph.py               # 童书生成工作流主图
│   │   ├── loop_graph.py          # 循环子图
│   │   ├── state.py               # 状态定义
│   │   └── nodes/                 # 工作流节点
│   ├── tools/
│   │   ├── search_faq_tool.py     # FAQ 搜索工具
│   │   └── risk_control_tool.py   # 风控检查工具
│   ├── storage/
│   │   ├── memory/                # 对话记忆存储
│   │   ├── database/              # 数据库存储
│   │   └── s3/                    # 对象存储
│   └── main.py                    # FastAPI 服务主入口
├── config/
│   ├── agent_llm_config.json      # Agent LLM 配置
│   ├── theme_analysis_llm_cfg.json  # 童书主题分析配置
│   ├── story_outline_llm_cfg.json   # 童书大纲配置
│   └── page_content_llm_cfg.json    # 童书页面内容配置
├── scripts/
│   ├── http_run.sh                # HTTP 服务启动脚本
│   ├── local_run.sh               # 本地运行脚本
│   ├── setup.sh                   # 环境配置脚本
│   └── pack.sh                    # 打包脚本
├── requirements.txt                # Python 依赖
├── pyproject.toml                 # 项目配置
└── README.md                      # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Git

### 安装依赖

```bash
# 安装依赖
pip install -r requirements.txt

# 或使用 uv
uv pip install -r requirements.txt
```

### 环境配置

在 `.env` 文件中配置以下环境变量：

```bash
# Coze 平台配置
COZE_WORKSPACE_PATH=/workspace/projects
COZE_WORKLOAD_IDENTITY_API_KEY=your_api_key_here
COZE_INTEGRATION_MODEL_BASE_URL=https://api.example.com
```

### 启动服务

#### 方式 1：启动 HTTP 服务（推荐）

```bash
bash scripts/http_run.sh -p 5000
```

服务将在 `http://localhost:5000` 启动，提供以下 API 接口：

- `POST /run` - 同步运行 Agent
- `POST /stream_run` - 流式运行 Agent
- `POST /cancel/{run_id}` - 取消执行
- `POST /node_run/{node_id}` - 运行单个节点
- `GET /health` - 健康检查
- `GET /graph_parameter` - 获取图参数

#### 方式 2：本地运行

```bash
# 运行完整流程
bash scripts/local_run.sh -m flow -i '{"query": "我想查询订单"}'

# 运行单个节点
bash scripts/local_run.sh -m node -n theme_analysis -i '{"theme": "友谊"}'
```

## 📡 API 使用示例

### 1. 同步运行 Agent

```bash
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{
    "type": "query",
    "session_id": "session_123",
    "message": "我想查询我的订单",
    "content": {
      "query": {
        "prompt": [
          {
            "type": "text",
            "content": {"text": "我想查询我的订单"}
          }
        ]
      }
    }
  }'
```

### 2. 流式运行 Agent

```bash
curl -X POST http://localhost:5000/stream_run \
  -H "Content-Type: application/json" \
  -d '{
    "type": "query",
    "session_id": "session_123",
    "message": "怎么申请退款？"
  }'
```

### 3. 取消执行

```bash
curl -X POST http://localhost:5000/cancel/run_id_123
```

## 🔧 Agent 核心能力

### 1. 风控检查

每个用户输入都会先进行风控检查，确保服务安全：

```python
# 风控检查结果
- 安全（Low Risk）：正常处理
- 中风险（Medium Risk）：谨慎回答，提示保护隐私
- 高风险（High Risk）：拒绝回答，提示规范提问
```

### 2. FAQ 知识库检索

从知识库中检索相关客服信息，确保回答准确：

```python
# 检索示例
search_faq(query="如何查询订单")
# 返回：相关知识库条目
```

### 3. 意图识别

自动识别用户咨询类型：

- **订单查询**：订单状态、订单详情
- **退款流程**：退款申请、退货条件
- **物流追踪**：配送进度、运单查询
- **支付问题**：支付方式、支付失败
- **其他咨询**：商品、优惠、售后等

### 4. 多轮对话记忆

支持上下文理解，记住用户历史对话：

```python
# 默认保留最近 20 轮对话（40 条消息）
MAX_MESSAGES = 40
```

## 🎨 可选功能：英文童书生成工作流

本项目还包含一个完整的英文童书生成工作流，支持根据主题自动生成带互动元素的童书。

### 工作流结构

```
输入参数
   ↓
[主题分析] → [故事大纲]
   ↓
[页面内容生成] + [角色图生成]
   ↓
[插画生成]
   ↓
[HTML生成] + [PDF生成]
   ↓
[输出整合] → 最终结果
```

### 使用童书生成工作流

```bash
# 运行童书生成流程
bash scripts/local_run.sh -m flow -i '{
  "theme": "A shy turtle learns to make friends",
  "age_group": "7-9",
  "style": "watercolor",
  "education_tags": ["friendship", "courage"],
  "page_count": 8
}'
```

## 🔍 技术栈

- **AI 模型**：豆包大语言模型 (doubao-seed-1-8-251228)
- **Agent 框架**：LangGraph
- **Web 框架**：FastAPI
- **HTTP 服务**：Uvicorn
- **对象存储**：S3SyncStorage（Coze 平台内置）

## 📝 配置说明

### Agent 配置文件

`config/agent_llm_config.json` - 智能 Agent 配置

```json
{
  "config": {
    "model": "doubao-seed-1-8-251228",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_completion_tokens": 10000,
    "timeout": 600,
    "thinking": "disabled"
  },
  "tools": [
    "risk_control_check",
    "search_faq"
  ],
  "sp": "Agent 系统提示词..."
}
```

### 童书生成配置文件

- `config/theme_analysis_llm_cfg.json` - 主题分析配置
- `config/story_outline_llm_cfg.json` - 故事大纲配置
- `config/page_content_llm_cfg.json` - 页面内容配置

## 🐛 故障排查

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   lsof -i :5000

   # 更改端口
   bash scripts/http_run.sh -p 5001
   ```

2. **依赖安装失败**
   ```bash
   # 使用 uv 安装（更快）
   pip install uv
   uv pip install -r requirements.txt
   ```

3. **API 调用超时**
   ```bash
   # 在代码中调整超时时间
   TIMEOUT_SECONDS = 900  # 15分钟
   ```

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 👥 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📮 联系方式

- 项目地址：https://github.com/CheckedX/JD-Smart-CS-Agent
- 问题反馈：GitHub Issues

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Coze](https://www.coze.cn/) - AI Agent 开发平台
