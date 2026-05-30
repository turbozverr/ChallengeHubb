from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChallengeHub Backend API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    mysql_dsn: str = "mysql+pymysql://root:eMYQfXOKXnNegUNOfwejqfhnMSDBQBCs@mysql.railway.internal:3306/railway"
    google_client_id: str = "336495115484-kvskacmcgvrbijkmngn4sjljmuf370tu.apps.googleusercontent.com"
    google_client_secret: str = "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"
    youtube_redirect_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/integrations/youtube/callback"
    tiktok_client_key: str = "sbawvxbhvdcq7823x1"
    tiktok_client_secret: str = "TnGznx75vi7gNe8hDzKQ1U5TvyyJ0gKh"
    tiktok_redirect_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/integrations/tiktok/callback"
    stripe_publishable_key: str = "pk_test_51TbOgKGfPrFAXeac6INs4P6ST2wcg5ltrd9olyUe23VAFuWFd1BOyJ4K4lNDL08UDSIOZ2IujMSL2aDmKHfNbmUM00TJVLbz50"
    stripe_secret_key: str = "sk_test_51TbOgKGfPrFAXeacBxQAYjYjtEdL982l1Ci8hkOOVIjfmOMdp22BpPTwrMwMtmXR11BwNyrRGhb93iGxMzY7v54Y00EHj2Kisg"
    stripe_price_id: str = "price_1TbOm5GfPrFAXeacQGQ9OwFE"
    stripe_success_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/premium/success"
    stripe_cancel_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/premium/cancel"
    gemini_api_key: str = "AQ.Ab8RN6INGgP482foILxBi-egEbx5XU6c4WjxAD5kGDlOyVyhzA"  # "AQ.Ab8RN6Jjg8B2f04uiylQNmjhrfPc7jXh03YY1iyN9xXNdS2iZg"
    gemini_model: str = "gemini-2.5-flash"
    mobile_jobs_token: str = "chhub_mjob_8f3d1a7c9e4b2f6d5a0c1e9f7b3a6d2c4e8f1a9b7d6c5e3f0a2b4c6d8e1f9a7"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CH_")


settings = Settings()
