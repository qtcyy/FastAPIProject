# AI Agent Backend Project

## Project Overview

This is an AI intelligent assistant backend system based on FastAPI, integrating various AI tools and capabilities, supporting conversation history persistence and real-time streaming responses.

## Core Features

### Implemented Features

- **Intelligent Conversation System**:
  - Multi-turn conversations based on LangChain and LangGraph
  - **⏰ Time-Aware Functionality**: System automatically retrieves and displays current China Standard Time (GMT+8)
  - Enhanced accuracy for time-sensitive queries and precise answers for time-sensitive questions
- **Enhanced Tool Integration**:
  - 🔍 **Intelligent Web Search**:
    - Integrated search1api real-time search functionality
    - **NEW**: LLM intelligent summarization feature, automatically extracting core information from search results
    - **🎛️ Controllable Summarization**: Dynamically controlled via `summary_with_llm` parameter
    - Dual-layer output: Intelligent summary + detailed search results (with complete links)
    - Structured markdown format with important information automatically bolded
    - Deduplication and redundancy removal, information organized by importance
  - 🌐 **Web Crawling**:
    - Batch web content extraction and intelligent parsing
    - **NEW**: LLM intelligent summarization feature, automatically analyzing key information from multiple web pages
    - **🎛️ Controllable Summarization**: Dynamically controlled via `summary_with_llm` parameter
    - Comprehensive analysis of multi-page content, identifying correlations and complementarity
    - Structured markdown format with clear source attribution
  - 🧮 **Enhanced Mathematical Calculation Tools**:
    - Secure AST mathematical expression calculation (replacing unsafe eval)
    - Support for 40+ mathematical functions: trigonometric functions, logarithms, exponentials, statistical functions, etc.
    - Descriptive statistical analysis: mean, median, standard deviation, quartiles, etc.
    - Distribution analysis: skewness, kurtosis, normality testing
    - Probability calculations: normal distribution parameter estimation, Z-score calculation
    - Support for list operations and complex mathematical expressions
  - 📊 **Database Queries**: Query student grades and other data through MCP client
- **MCP Tool Result Intelligent Processing**:
  - Support for multiple processing modes: raw, summary, formatted, filtered, structured
  - Automatically optimize tool output readability and practicality
  - Intelligently recognize and process different types of tool results
- **Structured Output**: Parse LLM output into Python objects
- **Conversation History Management**:
  - PostgreSQL-based persistent storage
  - Support for message editing, deletion, history queries
  - Multi-threaded conversation management
  - **Intelligent Conversation Naming**: LLM-based automatic title generation, accurately summarizing conversation topics
- **Multi-Model Support**: Support for DeepSeek, OpenAI-compatible APIs
- **Streaming Responses**: Server-Sent Events real-time conversation experience
- **Cross-Origin Support**: CORS middleware configured to support cross-origin requests from all sources
- **Multi-Agent Testing Framework**: Support for parallel and sequential multi-agent collaboration testing

## Technical Architecture

### Backend Framework
- **FastAPI**: High-performance asynchronous web framework
- **LangChain**: LLM application development framework
- **LangGraph**: State graph management and tool orchestration
- **PostgreSQL**: Conversation history persistent storage

### AI Integration
- **DeepSeek API**: Primary LLM service provider (Default: Qwen/Qwen2.5-7B-Instruct)
- **Multi-Tool System**: Intelligent search, secure computation, data queries, batch crawling, etc.
- **Intelligent Summarization Engine**: Dedicated LLM model for intelligent summarization and information extraction of search results and web crawling content
- **Dynamic Time Awareness**: Automatically update current time information for each conversation, improving time-sensitive query accuracy
- **MCP Client**: Model Context Protocol client integration
- **Streaming Responses**: Real-time conversation experience based on Server-Sent Events

## Quick Start

### Environment Requirements
- Python 3.8+
- PostgreSQL database
- API keys (DeepSeek/OpenAI compatible services)

### Install Dependencies
```bash
pip install fastapi uvicorn langchain langchain-anthropic langchain-deepseek langchain-openai langgraph psycopg asyncpg fastmcp pytz
```

### Database Configuration
Ensure PostgreSQL service is running and create database:
```sql
CREATE DATABASE chatbot;
```

### Start Service
```bash
# Development mode
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Conversation Endpoints
- `POST /chat/tools` - Intelligent conversation with tools
  - **Request Parameters**:
    ```json
    {
      "thread_id": "string",      // Thread ID
      "query": "string",          // User question
      "model": "string",          // Optional: model name, default "Qwen/Qwen2.5-7B-Instruct"
      "summary_with_llm": false   // Optional: enable LLM intelligent summarization, default false
    }
    ```
  - **Summarization Feature Control**:
    - `summary_with_llm: true` → Search results and web crawling content processed through LLM intelligent summarization
    - `summary_with_llm: false` → Return original formatted results
- `GET /chat/history/{thread_id}` - Get conversation history
- `DELETE /chat/history/{thread_id}` - Delete conversation thread

### Message Management
- `GET /chat/message/{thread_id}/{message_id}` - Get specific message by message ID
- `POST /chat/history/edit` - Edit message (by index)
- `POST /chat/history/edit/id` - Edit message (by ID)
- `POST /chat/history/delete` - Delete message
- `POST /chat/history/delete/after` - Delete all messages after specified message

### Intelligent Features
- `POST /chat/name/{thread_id}` - **Intelligent Conversation Naming**: Automatically generate concise and meaningful titles based on conversation content
  - **Features**:
    - Analyze the first few rounds of conversation content to extract core topics
    - Generate concise titles of 8-15 characters
    - Intelligently identify different types like technical questions, daily conversations, etc.
    - Automatically filter redundant words and highlight key information
  - **Return Format**:
    ```json
    {
      "thread_id": "string",
      "title": "Generated conversation title",
      "status": "success"
    }
    ```

### Special Features
- `POST /house/` - Structured house information extraction

## Project Structure

```
FastAPIProject/
├── main.py                     # FastAPI application entry point
├── config.py                   # Global configuration file
├── CLAUDE.md                   # Claude Code project guide
├── SECURITY.md                 # Security documentation
├── controller/                 # Controller layer (with __init__.py)
│   ├── __init__.py            # Python package initialization
│   ├── LLMController.py       # LLM-related endpoints
│   └── UserController.py      # User-related endpoints
├── service/                   # Service layer (with __init__.py)
│   ├── __init__.py
│   ├── LLMService.py
│   └── impl/
│       ├── __init__.py
│       └── LLMServiceImpl.py
├── llm/                       # AI functionality modules (with __init__.py)
│   ├── __init__.py
│   ├── llm_chat_with_tools/   # Conversation system with tools
│   │   ├── __init__.py
│   │   ├── README.md          # Module detailed documentation
│   │   ├── chatbot/           # ChatBot core implementation
│   │   │   ├── __init__.py
│   │   │   └── ChatBot.py
│   │   └── tools/             # Tool integration
│   │       ├── __init__.py
│   │       ├── calculate_tools.py    # Enhanced mathematical calculation tools
│   │       ├── search_tools.py       # Intelligent search and crawling tools (with LLM summarization)
│   │       └── result_processor.py   # MCP result processor
│   ├── llm_praser/            # Output parsing
│   │   ├── __init__.py
│   │   ├── llm_func.py
│   │   ├── llm_graph.py
│   │   ├── llm_out.py
│   │   └── llm_schema.py
│   └── llm_chat/              # Basic conversation
│       ├── __init__.py
│       ├── chat_graph.py
│       ├── chat_schema.py
│       └── llm_func.py
├── dao/                       # Data access layer (with __init__.py)
│   ├── __init__.py
│   ├── entity/
│   └── test/
│       ├── __init__.py
│       ├── SQLTest.py
│       ├── file_test.py
│       └── file.txt
├── vo/                        # Data transfer objects (with __init__.py)
│   ├── __init__.py
│   ├── BatchDeleteRequest.py
│   ├── ChatAgentRequest.py
│   ├── EditMessageRequest.py
│   └── HouseInfoRequest.py
├── Test/                      # Test modules (with __init__.py)
│   ├── __init__.py
│   ├── multi_agent.py         # Multi-agent testing framework
│   └── multi_agent_test_report.json  # Test reports
├── test_enhanced_calculate.py # Calculation tool tests
├── test_chat_naming.py        # Conversation naming tests
├── test_result_processing.py  # Result processing tests
└── test_main.http             # API test files
```

## Development Guide

### Environment Variable Configuration
The project uses `config.py` for unified configuration management, including:
- API keys (DeepSeek, search services, etc.)
- Database connection information
- MCP server configuration
- External service endpoints

### Code Structure Optimization
The project has completed Python package structure optimization:
- ✅ All directories contain `__init__.py` files
- ✅ Standard Python package import structure
- ✅ Better IDE support and code completion
- ✅ Clear module boundaries and dependency relationships

### Testing
- Use `test_main.http` files to test API endpoints
- Visit `http://localhost:8000/docs` to view auto-generated API documentation
- Run `python test_enhanced_calculate.py` to test mathematical calculation functionality
- Run `python Test/multi_agent.py` to test multi-agent collaboration functionality
- Run `python test_chat_naming.py` to test intelligent conversation naming functionality
- Run `python test_result_processing.py` to test result processing functionality
- Run database test files in `dao/test/`

### Extension Features
- Add new tool functions in the `llm/llm_chat_with_tools/tools/` directory
- Add new API endpoints in `controller/`
- Define new request/response models in `vo/`
- Integrate external services and tools through MCP client
- Refer to `llm/llm_chat_with_tools/README.md` for tool development details

### Documentation Structure
- `CLAUDE.md` - Claude Code integration and development guide
- `SECURITY.md` - Project security documentation and best practices
- `llm/llm_chat_with_tools/README.md` - Tool module detailed documentation
- `readme.md` - Main project documentation (Chinese version)
- `readme-en.md` - Main project documentation (this file)

## Security Features

- **Secure Computation**: Use AST parsing instead of eval to prevent code injection
- **Input Validation**: Pydantic model validation for all API inputs
- **Result Processing**: MCP tool result intelligent filtering and formatting
- **Database Security**: Use parameterized queries to prevent SQL injection

## Notes

- Ensure PostgreSQL database is running properly
- Configure correct API keys and service endpoints
- Production environment requires appropriate security configuration
- Pay attention to API call rate limits
- MCP servers need to be started and configured separately

## Use Cases

### 1. Information Search and Research
- Real-time news queries
- Academic material search
- Product information comparison
- Technical documentation lookup

### 2. Data Analysis and Computation
- Mathematical formula calculations
- Statistical data analysis
- Scientific computing
- Financial calculations

### 3. Content Organization and Summarization
- Web content extraction
- Multi-source information integration
- Intelligent summary generation
- Structured data processing

### 4. Conversation Management
- Long-term conversation history
- Conversation branch management
- Message editing and deletion
- Batch operations

## Performance Optimization

### Asynchronous Architecture
- Full asynchronous I/O operations
- Concurrent tool execution
- Streaming responses to reduce latency

### Caching Strategy
- Database connection pooling
- Tool result caching
- State snapshot mechanism

### Resource Management
- Automatic connection management
- Memory usage optimization
- Error recovery mechanism

## Update History

- **v1.0**: Basic tool integration and conversation management
- **v1.1**: Added LLM intelligent summarization functionality
- **v1.2**: Enhanced secure computation and result processing
- **v1.3**: Optimized time awareness and conversation naming
- **v1.4**: Support for batch operations and advanced mathematical tools
- **v1.5**: Code structure optimization with proper Python package structure

## License

This project follows the license agreement in the project root directory.

---

**Note**: Please ensure all required API keys and database connections are properly configured before use.