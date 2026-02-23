import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = "8446253574:AAG0nu6A5Ich-Vu65ryOgnudaqegEepaHB4"
    PROXY6_API_KEY: str = "4dbaf82e5e-35d6ccc64a-4ca7986c2e"
    CRYPTOBOT_API_TOKEN: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///bot.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
