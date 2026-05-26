from pydantic import BaseModel, EmailStr, Field


class MobileRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=255)


class MobileLoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class MobileUserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    avatar_url: str | None = None
    bio: str | None = None
    xp: int
    is_premium: bool
    status: str
    created_at: str


class MobileTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MobileUserResponse


class UpdateMobileProfileRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=64)
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None


class PinBadgesRequest(BaseModel):
    badge_ids: list[str] = Field(max_length=3)


class MobileChallengeResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    duration_days: int
    xp_reward: int
    challenge_type: str
    status: str
    created_at: str
    creator_name: str | None = None


class CreateMobileChallengeRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    difficulty: str = "normal"
    duration_days: int = Field(default=7, ge=1, le=60)
    xp_reward: int = Field(default=100, ge=1, le=500)


class JoinChallengeRequest(BaseModel):
    challenge_type: str


class ChallengeParticipationResponse(BaseModel):
    id: str
    user_id: str
    challenge_id: str
    challenge_type: str
    status: str
    started_at: str
    completed_at: str | None = None


class MobileVideoResponse(BaseModel):
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
    views_count: int
    likes_count: int
    shares_count: int
    created_at: str
    liked_by_me: bool = False
    comments_count: int = 0
    author_display_name: str | None = None
    author_username: str | None = None
    author_avatar_url: str | None = None
    challenge_title: str | None = None
    challenge_xp_reward: int | None = None


class CreateCommentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: str
    video_id: str
    user_id: str
    username: str
    display_name: str | None = None
    text: str
    created_at: str


class ReportVideoRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class BadgeResponse(BaseModel):
    id: str
    badge_code: str
    title: str
    description: str
    is_pinned: bool
    created_at: str


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: str
    username: str
    full_name: str
    avatar_url: str | None = None
    xp: int


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    is_read: bool
    created_at: str


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class AssistantResponse(BaseModel):
    answer: str
    suggested_challenge_id: str | None = None


class PremiumCheckoutResponse(BaseModel):
    checkout_url: str


class FcmTokenRequest(BaseModel):
    token: str = Field(min_length=10)
