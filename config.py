"""
配置管理模块
用于加载环境变量和配置项
"""

import os
from typing import Optional
from pathlib import Path


def load_env_file(env_file: str = ".env") -> None:
    """
    手动加载.env文件中的环境变量
    :param env_file: 环境变量文件路径
    """
    env_path = Path(__file__).parent / env_file
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


class Config:
    """配置类，集中管理所有配置项"""

    def __init__(self):
        # 加载.env文件
        load_env_file()

    # API密钥配置
    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def openai_api_base(self) -> str:
        return os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    @property
    def deepseek_api_key(self) -> str:
        return os.getenv("DEEPSEEK_API_KEY", "")

    @property
    def deepseek_api_base(self) -> str:
        return os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

    # 数据库配置
    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", "postgresql://localhost:5432/chatbot")

    @property
    def mysql_url(self) -> str:
        return os.getenv("MYSQL_URL", "")

    # 搜索API配置
    @property
    def search_api_key(self) -> str:
        return os.getenv("SEARCH_API_KEY", "")

    @property
    def search_api_url(self) -> str:
        return os.getenv("SEARCH_API_URL", "https://api.search1api.com/search")

    @property
    def crawl_api_url(self) -> str:
        return os.getenv("CRAWL_API_URL", "https://api.search1api.com/crawl")

    # MCP服务器配置
    @property
    def mcp_server_url(self) -> str:
        return os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")

    def validate(self) -> None:
        """验证必要的配置项是否存在"""
        required_configs = [
            ("OPENAI_API_KEY", self.openai_api_key),
            ("DEEPSEEK_API_KEY", self.deepseek_api_key),
            ("SEARCH_API_KEY", self.search_api_key),
        ]

        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)

        if missing_configs:
            raise ValueError(f"缺少必要的配置项: {', '.join(missing_configs)}")


# 全局配置实例
config = Config()
