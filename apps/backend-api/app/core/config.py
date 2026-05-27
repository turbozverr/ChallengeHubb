from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChallengeHub Backend API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    mysql_dsn: str = "mysql+pymysql://challengehub:challengehub@localhost:3306/challengehub"
    google_client_id: str = "336495115484-kvskacmcgvrbijkmngn4sjljmuf370tu.apps.googleusercontent.com"
    google_client_secret: str = "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"
    youtube_redirect_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/integrations/youtube/callback"
    stripe_publishable_key: str = "pk_test_51TbOgKGfPrFAXeac6INs4P6ST2wcg5ltrd9olyUe23VAFuWFd1BOyJ4K4lNDL08UDSIOZ2IujMSL2aDmKHfNbmUM00TJVLbz50"
    stripe_secret_key: str = "sk_test_51TbOgKGfPrFAXeacBxQAYjYjtEdL982l1Ci8hkOOVIjfmOMdp22BpPTwrMwMtmXR11BwNyrRGhb93iGxMzY7v54Y00EHj2Kisg"
    stripe_price_id: str = "price_1TbOm5GfPrFAXeacQGQ9OwFE"
    stripe_success_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/premium/success"
    stripe_cancel_url: str = "https://challengehubb-production.up.railway.app/api/v1/mobile/premium/cancel"
    gemini_api_key: str = "AQ.Ab8RN6LAzpYc3TA1FceXBM6sRT5A8IXIn_Jwr4NTcRb2EVJs0g"
    gemini_model: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CH_")


settings = Settings()
