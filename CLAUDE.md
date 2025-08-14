# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based AI agent backend that provides LLM chat capabilities with tool integration. The system supports:

- LLM chat with web search and calculation tools
- Structured output parsing for specific domains (e.g., house information)
- PostgreSQL-based conversation history persistence
- Multiple LLM providers (DeepSeek, OpenAI-compatible APIs)

## Architecture

### Core Components

- **FastAPI Application**: Entry point in `main.py` that includes router controllers
- **Controller Layer**: REST API endpoints in `controller/`
  - `LLMController`: Chat, history management, message editing endpoints
  - `SecurityController`: Security-related endpoints
- **Service Layer**: Business logic in `service/` and `service/impl/`
  - `LLMServiceImpl`: Main service implementing chat and history operations
- **LLM Layer**: AI functionality in `llm/`
  - `llm_chat_with_tools/`: ChatBot with tool integration using LangGraph
  - `llm_praser/`: Structured output parsing
  - `llm_chat/`: Basic chat functionality
- **Data Layer**: `dao/` for data access, `vo/` for value objects

### Key Architecture Patterns

- **Tool Integration**: Uses LangGraph for orchestrating LLM calls with external tools
- **Streaming Responses**: Chat endpoints return Server-Sent Events (SSE) for real-time streaming
- **State Management**: PostgreSQL checkpointer for conversation persistence
- **Async/Await**: Fully asynchronous implementation throughout

### Tool System

The ChatBot integrates several tools via LangGraph:
- `search_tool`: Web search via search1api.com
- `web_crawler`: Batch web page content extraction
- `calculate_tools`: Enhanced mathematical calculations with safe evaluation
- `advanced_math`: Statistical analysis and advanced mathematical operations
- `query_student_avg_grade`: Database queries via MCP client

## Development Commands

### Running the Application
```bash
# Start FastAPI development server
uvicorn main:app --reload

# Or if using a different port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run tests (if pytest is configured)
python -m pytest

# Run specific test files
python dao/test/SQLTest.py
python dao/test/file_test.py
```

### Dependencies
The project uses several key dependencies:
- `fastapi`: Web framework
- `langchain`, `langchain-anthropic`, `langchain-deepseek`, `langchain-openai`: LLM integrations
- `langgraph`: Agent orchestration and state management
- `psycopg`, `asyncpg`: PostgreSQL async drivers
- `fastmcp`: MCP client for tool integration

## Database Setup

The system requires PostgreSQL for conversation persistence:
- Database: `chatbot`
- Connection: `postgresql://qtcyy:12345678@localhost:5432/chatbot`
- Auto-initialized via `AsyncPostgresSaver.setup()`

## API Endpoints

### Chat Endpoints
- `POST /chat/tools`: Main chat with tools
- `GET /chat/history/{thread_id}`: Get conversation history
- `DELETE /chat/history/{thread_id}`: Delete entire thread

### Message Management
- `POST /chat/history/edit`: Edit message by index
- `POST /chat/history/edit/id`: Edit message by ID
- `POST /chat/history/delete`: Delete message by index
- `POST /chat/history/delete/id`: Delete message by ID
- `POST /chat/history/delete/after`: Delete all messages after specified ID

### Specialized Endpoints
- `POST /house/`: Structured house information extraction

## Configuration

### Environment Variables
Key configurations are set in the ChatBot class:
- API keys and endpoints for various LLM providers
- PostgreSQL connection details
- External service configurations (search APIs, MCP servers)

### Model Configuration
Default model: `Qwen/Qwen2.5-7B-Instruct` via DeepSeek API
- Temperature: 0.8
- Supports model switching via API requests

## Development Notes

### Code Conventions
- Async/await pattern throughout
- Chinese comments and docstrings
- FastAPI dependency injection pattern
- Pydantic models for request/response validation

### Key Files to Understand
- `llm/llm_chat_with_tools/chatbot/ChatBot.py`: Core chatbot implementation
- `llm/llm_chat_with_tools/tools/search_tools.py`: Tool definitions
- `controller/LLMController.py`: API endpoint definitions
- `service/impl/LLMServiceImpl.py`: Service layer implementation

### Testing Strategy
- Unit tests in `dao/test/`
- HTTP endpoint testing via `test_main.http`
- Manual testing through FastAPI's automatic OpenAPI docs at `/docs`