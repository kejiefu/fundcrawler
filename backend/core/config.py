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

    secret_key: str = "your-secret-key-change-this-in-production-2024"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    debug: bool = False

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
