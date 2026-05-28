from pydantic import BaseModel


class CreateSponsoredChallengeRequest(BaseModel):
    title: str
    description: str
    reward_text: str
    difficulty: str = "normal"
    duration_days: int = 7
    xp_reward: int = 100
    promo_mode: str = "SINGLE"
    promo_single_code: str | None = None
    promo_codes: list[str] | None = None
    client_id: str


class UpdateSponsoredChallengeRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    reward_text: str | None = None
    difficulty: str | None = None
    duration_days: int | None = None
    xp_reward: int | None = None
    promo_mode: str | None = None
    promo_single_code: str | None = None
    promo_codes: list[str] | None = None
    status: str | None = None


class SponsoredChallengeResponse(BaseModel):
    id: str
    title: str
    description: str
    reward_text: str
    difficulty: str
    duration_days: int
    xp_reward: int
    promo_mode: str
    promo_single_code: str | None = None
    client_id: str
    client_company_name: str
    status: str
    created_by_admin_id: str
    created_at: str
    published_at: str | None = None


class PromoCodeResponse(BaseModel):
    id: str
    challenge_id: str
    code: str
    is_sent: bool


class AdVideoResponse(BaseModel):
    id: str
    description: str | None = None
    url: str | None = None
    file_path: str | None = None
    status: str
    created_by_admin_id: str | None = None
    views_count: int = 0
    likes_count: int = 0
    shares_count: int = 0
    created_at: str
