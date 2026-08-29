from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    PROJECT_NAME: str = "RecoverX"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI Revenue Recovery Twin"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./recoverx.db"
    REDIS_URL: Optional[str] = None
    
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    MODEL_NAME: str = "gpt-4"
    
    DEMO_MODE: bool = True
    
    MAX_RETRIES_PER_TRANSACTION: int = 3
    RETRY_COOLDOWN_MINUTES: int = 15
    MAX_RECOVERY_ATTEMPTS_PER_CUSTOMER: int = 5
    DEFAULT_DAILY_RECOVERY_BUDGET: float = 5000.0
    MAX_AUTO_RECOVERY_AMOUNT: float = 50000.0
    
    ML_MODEL_PATH: str = "ml/models"
    
    @property
    def is_demo_mode(self) -> bool:
        return self.DEMO_MODE or not self.RAZORPAY_KEY_ID

settings = Settings()
