from pydantic import BaseModel


class CampaignStatsResponse(BaseModel):
    challenge_id: str
    title: str
    client_company_name: str
    views: int
    completed: int
    conversion_rate: float


class DateValuePoint(BaseModel):
    date: str
    value: float


class MobileRegistrationsPoint(BaseModel):
    date: str
    users: int


class TopChallengePoint(BaseModel):
    challenge_id: str
    title: str
    submissions: int
    views: int
    shares: int
    completion_rate: float


class ContentGrowthPoint(BaseModel):
    date: str
    ad_videos: int
    regular_videos: int


class AdminDashboardAnalyticsResponse(BaseModel):
    dau_wau_mau: list[DateValuePoint]
    mobile_registrations: list[MobileRegistrationsPoint]
    moderation_decision_time_hours: list[DateValuePoint]
    top_challenges_engagement: list[TopChallengePoint]
    content_growth: list[ContentGrowthPoint]
    ai_quality_overturned_rate: list[DateValuePoint]


class InteractionPoint(BaseModel):
    date: str
    likes: int
    shares: int
    comments: int


class BusinessDashboardAnalyticsResponse(BaseModel):
    views_by_day: list[DateValuePoint]
    submissions_by_day: list[DateValuePoint]
    completed_by_day: list[DateValuePoint]
    conversion_by_day: list[DateValuePoint]
    interactions_by_day: list[InteractionPoint]
