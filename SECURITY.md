# 安全配置说明

## 配置文件管理

为了确保API密钥和敏感信息的安全，本项目采用了外部配置文件的方式：

### 文件结构

- `.env.example` - 配置文件示例，包含所有必要的配置项模板
- `.env` - 实际配置文件，包含真实的API密钥（已在git中排除）
- `config.py` - 配置管理模块，负责加载和验证配置

### 首次设置

1. 复制示例配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入真实的API密钥：
   ```env
   OPENAI_API_KEY=your_real_api_key_here
   DEEPSEEK_API_KEY=your_real_deepseek_key_here
   SEARCH_API_KEY=your_real_search_key_here
   # ... 其他配置项
   ```

### 安全措施

- ✅ `.env` 文件已添加到 `.gitignore`，不会被提交到版本控制
- ✅ 所有硬编码的API密钥已移除
- ✅ 配置加载时会自动验证必要的配置项
- ✅ 使用了命名空间避免与LangGraph的config参数冲突

### 配置项说明

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI兼容API密钥 | ✅ |
| `OPENAI_API_BASE` | OpenAI兼容API基础URL | ❌ |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | ✅ |
| `DEEPSEEK_API_BASE` | DeepSeek API基础URL | ❌ |
| `DATABASE_URL` | PostgreSQL数据库连接字符串 | ❌ |
| `SEARCH_API_KEY` | 搜索API密钥 | ✅ |
| `SEARCH_API_URL` | 搜索API URL | ❌ |
| `CRAWL_API_URL` | 网页爬取API URL | ❌ |
| `MCP_SERVER_URL` | MCP服务器URL | ❌ |

### 使用方法

在代码中使用配置：

```python
from config import config as app_config

# 使用配置
api_key = app_config.openai_api_key
database_url = app_config.database_url
```

### 注意事项

1. **永远不要**将 `.env` 文件提交到版本控制
2. **定期轮换**API密钥
3. **使用最小权限**原则配置API密钥
4. **在生产环境**中使用环境变量而不是文件
5. **备份重要配置**，但确保备份也是安全的