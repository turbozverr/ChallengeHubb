from pydantic import BaseModel


class ModerationVideoResponse(BaseModel):
    id: str
    challenge_id: str
    challenge_type: str = "SPONSORED"
    author_user_id: str
    url: str
    description: str | None = None
    ai_status: str
    status: str
    reports_count: int
    is_ad: bool
    views_count: int = 0
    likes_count: int = 0
    shares_count: int = 0
    created_at: str
    decided_by: str | None = None
    decided_at: str | None = None


class ReportResponse(BaseModel):
    id: str
    video_id: str
    video_url: str | None = None
    reason: str
    status: str
    created_at: str
    decided_by: str | None = None
    decided_at: str | None = None


class ModerationDecisionRequest(BaseModel):
    decision: str


class UpdateVideoRequest(BaseModel):
    url: str | None = None
    description: str | None = None
    status: str | None = None
    is_ad: bool | None = None
