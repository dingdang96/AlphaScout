from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 数据库配置
    DB_URL: str

    # 网络代理
    PROXY_URL: Optional[str] = None

    # Twitter 抓取风控参数
    TWITTER_POLL_INTERVAL_MINUTES: int = 20
    TWITTER_BATCH_SIZE: int = 10
    TWITTER_DELAY_MIN: float = 8.0
    TWITTER_DELAY_MAX: float = 18.0
    TWITTER_AUTH_TOKEN: Optional[str] = None

    # 大模型服务
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"

    # 推送渠道
    TG_BOT_TOKEN: Optional[str] = None
    TG_CHAT_ID: Optional[str] = None
    FEISHU_WEBHOOK_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
