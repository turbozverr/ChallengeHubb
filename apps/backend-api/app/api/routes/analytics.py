from datetime import UTC, date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import AdVideoORM, MobileUserORM, ModerationVideoORM, SponsoredChallengeORM, UserChallengeORM, VideoCommentORM, VideoLikeORM, get_db
from app.schemas.analytics import (
    AdminDashboardAnalyticsResponse,
    BusinessDashboardAnalyticsResponse,
    CampaignStatsResponse,
    ContentGrowthPoint,
    DateValuePoint,
    InteractionPoint,
    MobileRegistrationsPoint,
    TopChallengePoint,
)
from app.schemas.auth import MeResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/campaigns", response_model=list[CampaignStatsResponse])
def get_campaign_stats(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> list[CampaignStatsResponse]:
    require_roles({WebRole.ADMIN, WebRole.BUSINESS_CLIENT}, current_user)
    challenges = db.execute(select(SponsoredChallengeORM)).scalars().all()
    if current_user.role == WebRole.BUSINESS_CLIENT:
        challenges = [c for c in challenges if c.client_id == current_user.id]

    result: list[CampaignStatsResponse] = []
    for challenge in challenges:
        videos = db.execute(
            select(ModerationVideoORM).where(
                ModerationVideoORM.challenge_id == challenge.id,
                ModerationVideoORM.challenge_type == "SPONSORED",
            )
        ).scalars().all()
        views = sum(v.views_count for v in videos)
        completed = len([v for v in videos if v.status == "PUBLISHED"])
        conversion = (completed / views) * 100 if views > 0 else 0
        result.append(
            CampaignStatsResponse(
                challenge_id=challenge.id,
                title=challenge.title,
                client_company_name=challenge.client_company_name,
                views=views,
                completed=completed,
                conversion_rate=round(conversion, 2),
            )
        )
    return result


@router.get("/admin-dashboard", response_model=AdminDashboardAnalyticsResponse)
def get_admin_dashboard_analytics(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> AdminDashboardAnalyticsResponse:
    require_roles({WebRole.ADMIN}, current_user)

    today = date.today()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    day_keys = [d.isoformat() for d in days]

    videos = db.execute(select(ModerationVideoORM)).scalars().all()
    ad_videos = db.execute(select(AdVideoORM)).scalars().all()
    challenges = db.execute(select(SponsoredChallengeORM)).scalars().all()
    user_challenges = db.execute(select(UserChallengeORM)).scalars().all()
    mobile_users = db.execute(select(MobileUserORM)).scalars().all()

    dau_wau_mau: list[DateValuePoint] = []
    for d in days:
        start = d
        dau_users = {v.author_user_id for v in videos if v.created_at.date() == start}
        wau_users = {v.author_user_id for v in videos if start - timedelta(days=6) <= v.created_at.date() <= start}
        mau_users = {v.author_user_id for v in videos if start - timedelta(days=29) <= v.created_at.date() <= start}
        dau_wau_mau.extend(
            [
                DateValuePoint(date=f"{d.isoformat()}|DAU", value=float(len(dau_users))),
                DateValuePoint(date=f"{d.isoformat()}|WAU", value=float(len(wau_users))),
                DateValuePoint(date=f"{d.isoformat()}|MAU", value=float(len(mau_users))),
            ]
        )

    mobile_reg_map = {key: 0 for key in day_keys}
    for user in mobile_users:
        key = user.created_at.date().isoformat()
        if key in mobile_reg_map:
            mobile_reg_map[key] += 1
    mobile_registrations = [MobileRegistrationsPoint(date=key, users=mobile_reg_map[key]) for key in day_keys]

    decision_map: dict[str, list[float]] = {key: [] for key in day_keys}
    for v in videos:
        if not v.decided_at:
            continue
        key = v.decided_at.date().isoformat()
        if key not in decision_map:
            continue
        hours = (v.decided_at - v.created_at).total_seconds() / 3600
        if hours >= 0:
            decision_map[key].append(hours)
    decision_time = [
        DateValuePoint(date=key, value=round(sum(vals) / len(vals), 2) if vals else 0.0)
        for key, vals in decision_map.items()
    ]

    by_challenge: dict[str, TopChallengePoint] = {}
    user_challenge_titles = {c.id: c.title for c in user_challenges}
    challenge_titles = {c.id: c.title for c in challenges}
    for v in videos:
        if v.challenge_id not in by_challenge:
            by_challenge[v.challenge_id] = TopChallengePoint(
                challenge_id=v.challenge_id,
                title=challenge_titles.get(v.challenge_id, user_challenge_titles.get(v.challenge_id, v.challenge_id)),
                submissions=0,
                views=0,
                shares=0,
                completion_rate=0,
            )
        item = by_challenge[v.challenge_id]
        item.submissions += 1
        item.views += v.views_count
        item.shares += v.shares_count
        if v.status == "PUBLISHED":
            item.completion_rate += 1
    top_challenges = list(by_challenge.values())
    for item in top_challenges:
        item.completion_rate = round((item.completion_rate / item.submissions) * 100, 2) if item.submissions else 0
    top_challenges.sort(key=lambda x: (x.views + x.shares * 3), reverse=True)
    top_challenges = top_challenges[:7]

    growth_map: dict[str, ContentGrowthPoint] = {
        key: ContentGrowthPoint(date=key, ad_videos=0, regular_videos=0) for key in day_keys
    }
    for v in videos:
        key = v.created_at.date().isoformat()
        if key not in growth_map:
            continue
        growth_map[key].regular_videos += 1
    for v in ad_videos:
        key = v.created_at.date().isoformat()
        if key in growth_map:
            growth_map[key].ad_videos += 1
    content_growth = [growth_map[key] for key in day_keys]

    ai_quality = []
    for key in day_keys:
        day_videos = [v for v in videos if v.decided_at and v.decided_at.date().isoformat() == key]
        if not day_videos:
            ai_quality.append(DateValuePoint(date=key, value=0.0))
            continue
        overturned = [
            v
            for v in day_videos
            if (v.ai_status == "APPROVED" and v.status == "BLOCKED")
            or (v.ai_status == "REJECTED" and v.status == "PUBLISHED")
        ]
        rate = (len(overturned) / len(day_videos)) * 100
        ai_quality.append(DateValuePoint(date=key, value=round(rate, 2)))

    return AdminDashboardAnalyticsResponse(
        dau_wau_mau=dau_wau_mau,
        mobile_registrations=mobile_registrations,
        moderation_decision_time_hours=decision_time,
        top_challenges_engagement=top_challenges,
        content_growth=content_growth,
        ai_quality_overturned_rate=ai_quality,
    )


@router.get("/business-dashboard", response_model=BusinessDashboardAnalyticsResponse)
def get_business_dashboard_analytics(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> BusinessDashboardAnalyticsResponse:
    require_roles({WebRole.ADMIN, WebRole.BUSINESS_CLIENT}, current_user)

    today = date.today()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    day_keys = [d.isoformat() for d in days]

    challenges = db.execute(select(SponsoredChallengeORM)).scalars().all()
    if current_user.role == WebRole.BUSINESS_CLIENT:
        challenges = [c for c in challenges if c.client_id == current_user.id]
    challenge_ids = {c.id for c in challenges}

    videos = db.execute(select(ModerationVideoORM)).scalars().all()
    videos = [v for v in videos if v.challenge_id in challenge_ids and v.challenge_type == "SPONSORED"]
    video_ids = {v.id for v in videos}
    comments = db.execute(select(VideoCommentORM)).scalars().all()
    likes_by_video = {
        vid: int(cnt)
        for vid, cnt in db.execute(
            select(VideoLikeORM.video_id, func.count(VideoLikeORM.id)).group_by(VideoLikeORM.video_id)
        ).all()
    }

    views_map = {k: 0 for k in day_keys}
    submissions_map = {k: 0 for k in day_keys}
    completed_map = {k: 0 for k in day_keys}
    likes_map = {k: 0 for k in day_keys}
    shares_map = {k: 0 for k in day_keys}
    comments_map = {k: 0 for k in day_keys}

    for v in videos:
        k = v.created_at.date().isoformat()
        if k not in views_map:
            continue
        views_map[k] += int(v.views_count)
        submissions_map[k] += 1
        likes_map[k] += likes_by_video.get(v.id, 0)
        shares_map[k] += int(v.shares_count)
        if v.status == "PUBLISHED":
            completed_map[k] += 1
    for comment in comments:
        if comment.video_id not in video_ids:
            continue
        k = comment.created_at.date().isoformat()
        if k in comments_map:
            comments_map[k] += 1

    views_by_day = [DateValuePoint(date=k, value=float(views_map[k])) for k in day_keys]
    submissions_by_day = [DateValuePoint(date=k, value=float(submissions_map[k])) for k in day_keys]
    completed_by_day = [DateValuePoint(date=k, value=float(completed_map[k])) for k in day_keys]
    conversion_by_day = [
        DateValuePoint(date=k, value=round((completed_map[k] / views_map[k]) * 100, 2) if views_map[k] > 0 else 0.0)
        for k in day_keys
    ]
    interactions_by_day = [
        InteractionPoint(date=k, likes=likes_map[k], shares=shares_map[k], comments=comments_map[k])
        for k in day_keys
    ]

    return BusinessDashboardAnalyticsResponse(
        views_by_day=views_by_day,
        submissions_by_day=submissions_by_day,
        completed_by_day=completed_by_day,
        conversion_by_day=conversion_by_day,
        interactions_by_day=interactions_by_day,
    )
