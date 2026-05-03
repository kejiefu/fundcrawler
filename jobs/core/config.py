import os
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    """Application configuration class, centrally manage all environment variables"""

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "999888777"
    db_name: str = "stock_fund_analysis"
    db_charset: str = "utf8mb4"

    debug: bool = False

    a_share_basic_sync_enabled: bool = True
    a_share_basic_sync_interval_seconds: int = 3600

    kline_sync_enabled: bool = True
    kline_sync_interval_seconds: int = 86400

    @property
    def database_url(self) -> str:
        """Generate database connection URL"""
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}"
            f"/{self.db_name}?charset={self.db_charset}"
        )

    class Config:
        env_file = ".env"

settings = AppSettings()
