import os
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    """应用配置类，集中管理所有环境变量"""

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "999888777"
    db_name: str = "admin_dashboard"
    db_charset: str = "utf8mb4"

    debug: bool = False

    a_share_basic_sync_enabled: bool = True
    a_share_basic_sync_interval_seconds: int = 3600

    @property
    def database_url(self) -> str:
        """生成数据库连接 URL"""
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}"
            f"/{self.db_name}?charset={self.db_charset}"
        )

    class Config:
        env_file = ".env"

settings = AppSettings()
