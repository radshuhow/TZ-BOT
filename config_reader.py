from pydantic import SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """
    Класс для загрузки и валидации настроек из .env файла.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # Токен бота
    bot_token: SecretStr = Field(..., env=["BOT_TOKEN", "bot_token"])

    # Строка подключения к MongoDB
    mongo_dsn: SecretStr = Field(..., env=["MONGO_DSN", "DB_URL", "mongo_dsn", "db_url"])
    # Имя БД для хранения FSM (опционально)
    mongo_db_name: str = Field(default="tz_bot_fsm_storage", env=["MONGO_DB_NAME", "mongo_db_name"])
    
    # ID целевого чата для отправки ТЗ
    target_chat_id: int = Field(..., env=["TARGET_CHAT_ID", "target_chat_id"])

    # Список ID пользователей, которым разрешен доступ к боту
    # В .env файле должен быть формат: ALLOWED_USERS=123,456
    allowed_users: List[int] = Field(..., env="ALLOWED_USERS")

# Создаем экземпляр настроек, который будет импортироваться в других файлах
config = Settings()