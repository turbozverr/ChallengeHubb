from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChallengeHub Backend API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    mysql_dsn: str = "mysql+pymysql://challengehub:challengehub@localhost:3306/challengehub"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CH_")


settings = Settings()
