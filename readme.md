# AI Agent 后端项目

## 项目简介

这是一个基于 FastAPI 的 AI 智能助手后端系统，集成了多种 AI 工具和功能，支持对话历史持久化和实时流式响应。

## 核心功能

### 已实现功能

- **智能对话系统**：
  - 基于 LangChain 和 LangGraph 的多轮对话
  - **⏰ 时间感知功能**：系统自动获取并显示当前中国标准时间 (GMT+8)
  - 增强时效性查询的准确性，为时间敏感问题提供精准回答
- **强化工具集成**：
  - 🔍 **智能网页搜索**：
    - 集成 search1api 实时搜索功能
    - **NEW**: LLM 智能总结功能，自动提炼搜索结果核心信息
    - **🎛️ 可控总结功能**：通过 `summary_with_llm` 参数动态控制
    - 双层输出：智能总结 + 详细搜索结果（含完整链接）
    - 结构化 markdown 格式，重点信息自动加粗
    - 去重去冗余，按重要性排序组织信息
  - 🌐 **网页爬取**：
    - 批量网页内容抓取和智能解析
    - **NEW**: LLM 智能总结功能，自动分析多个网页的关键信息
    - **🎛️ 可控总结功能**：通过 `summary_with_llm` 参数动态控制
    - 多网页内容综合分析，识别关联性和互补性
    - 结构化 markdown 格式，来源标注清晰
  - 🧮 **强化数学计算工具**：
    - 安全的 AST 数学表达式计算（替代不安全的 eval）
    - 支持 40+ 数学函数：三角函数、对数、指数、统计函数等
    - 描述性统计分析：均值、中位数、标准差、四分位数等
    - 分布分析：偏度、峰度、正态性检验
    - 概率计算：正态分布参数估计、Z分数计算
    - 支持列表运算和复杂数学表达式
  - 📊 **数据库查询**：通过 MCP 客户端查询学生成绩等数据
- **MCP 工具结果智能处理**：
  - 支持多种处理模式：原始、摘要、格式化、过滤、结构化
  - 自动优化工具输出的可读性和实用性
  - 智能识别和处理不同类型的工具结果
- **结构化输出**：将 LLM 输出解析为 Python 对象
- **对话历史管理**：
  - 基于 PostgreSQL 的持久化存储
  - 支持消息编辑、删除、历史查询
  - 多线程对话管理
  - **智能对话命名**：基于LLM的自动标题生成，准确概括对话主题
- **多模型支持**：支持 DeepSeek、OpenAI 兼容 API
- **流式响应**：Server-Sent Events 实时对话体验
- **跨域支持**：已配置 CORS 中间件，支持所有来源的跨域请求
- **多智能体测试框架**：支持并行和顺序多智能体协作测试

## 技术架构

### 后端框架
- **FastAPI**：高性能异步 Web 框架
- **LangChain**：LLM 应用开发框架
- **LangGraph**：状态图管理和工具编排
- **PostgreSQL**：对话历史持久化存储

### AI 集成
- **DeepSeek API**：主要 LLM 服务提供商（默认：Qwen/Qwen2.5-7B-Instruct）
- **多工具系统**：智能搜索、安全计算、数据查询、批量爬取等
- **智能总结引擎**：专用 LLM 模型对搜索结果和网页爬取内容进行智能总结和信息提炼
- **动态时间感知**：每次对话自动更新当前时间信息，提升时效性查询准确性
- **MCP 客户端**：Model Context Protocol 客户端集成
- **流式响应**：基于 Server-Sent Events 的实时对话体验

## 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 数据库
- API 密钥（DeepSeek/OpenAI 兼容服务）

### 安装依赖
```bash
pip install fastapi uvicorn langchain langchain-anthropic langchain-deepseek langchain-openai langgraph psycopg asyncpg fastmcp pytz
```

### 数据库配置
确保 PostgreSQL 服务运行，并创建数据库：
```sql
CREATE DATABASE chatbot;
```

### 启动服务
```bash
# 开发模式
uvicorn main:app --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API 接口

### 对话接口
- `POST /chat/tools` - 带工具的智能对话
  - **请求参数**：
    ```json
    {
      "thread_id": "string",      // 线程ID
      "query": "string",          // 用户问题
      "model": "string",          // 可选：模型名称，默认 "Qwen/Qwen2.5-7B-Instruct"
      "summary_with_llm": false   // 可选：是否启用LLM智能总结，默认 false
    }
    ```
  - **总结功能控制**：
    - `summary_with_llm: true` → 搜索结果和网页爬取内容经过LLM智能总结
    - `summary_with_llm: false` → 返回原始格式化结果
- `GET /chat/history/{thread_id}` - 获取对话历史
- `DELETE /chat/history/{thread_id}` - 删除对话线程

### 消息管理
- `GET /chat/message/{thread_id}/{message_id}` - 根据消息ID获取指定消息
- `POST /chat/history/edit` - 编辑消息（按索引）
- `POST /chat/history/edit/id` - 编辑消息（按ID）
- `POST /chat/history/delete` - 删除消息
- `POST /chat/history/delete/after` - 删除指定消息之后的所有消息

### 智能功能
- `POST /chat/name/{thread_id}` - **智能对话命名**：根据对话内容自动生成简洁有意义的标题
  - **功能特点**：
    - 分析对话前几轮内容，提取核心主题
    - 生成8-15字符的简洁标题
    - 智能识别技术问题、日常对话等不同类型
    - 自动过滤冗余词汇，突出关键信息
  - **返回格式**：
    ```json
    {
      "thread_id": "string",
      "title": "生成的对话标题",
      "status": "success"
    }
    ```

### 特殊功能
- `POST /house/` - 房屋信息结构化提取

## 项目结构

```
FastAPIProject/
├── main.py                     # FastAPI 应用入口
├── controller/                 # 控制器层
│   ├── LLMController.py       # LLM 相关接口
│   └── SecurityController.py  # 安全相关接口
├── service/                   # 服务层
│   ├── LLMService.py
│   └── impl/LLMServiceImpl.py
├── llm/                       # AI 功能模块
│   ├── llm_chat_with_tools/   # 带工具的对话系统
│   │   ├── chatbot/           # ChatBot 核心实现
│   │   │   └── ChatBot.py
│   │   └── tools/             # 工具集成
│   │       ├── calculate_tools.py    # 强化数学计算工具
│   │       ├── search_tools.py       # 智能搜索和爬取工具（含LLM总结）
│   │       └── result_processor.py   # MCP结果处理器
│   ├── llm_praser/            # 输出解析
│   └── llm_chat/              # 基础对话
├── dao/                       # 数据访问层
├── vo/                        # 数据传输对象
├── Test/                      # 测试模块
│   ├── multi_agent.py         # 多智能体测试框架
│   └── multi_agent_test_report.json  # 测试报告
├── test_enhanced_calculate.py # 计算工具测试
└── test_main.http             # API 测试文件
```

## 开发说明

### 配置环境变量
在 ChatBot 类中配置相关 API 密钥和数据库连接信息。

### 测试
- 使用 `test_main.http` 文件测试 API 接口
- 访问 `http://localhost:8000/docs` 查看自动生成的 API 文档
- 运行 `python test_enhanced_calculate.py` 测试数学计算功能
- 运行 `python Test/multi_agent.py` 测试多智能体协作功能
- 运行 `python test_chat_naming.py` 测试智能对话命名功能
- 运行 `dao/test/` 中的数据库测试文件

### 扩展功能
- 在 `llm/llm_chat_with_tools/tools/` 目录下添加新的工具函数
- 在 `controller/` 中添加新的 API 端点
- 在 `vo/` 中定义新的请求/响应模型
- 通过 MCP 客户端集成外部服务和工具

## 安全特性

- **安全计算**：使用 AST 解析替代 eval，防止代码注入
- **输入验证**：Pydantic 模型验证所有 API 输入
- **结果处理**：MCP 工具结果智能过滤和格式化
- **数据库安全**：使用参数化查询防止 SQL 注入

## 注意事项

- 确保 PostgreSQL 数据库正常运行
- 配置正确的 API 密钥和服务端点
- 生产环境需要适当的安全配置
- 注意 API 调用频率限制
- MCP 服务器需要单独启动和配置