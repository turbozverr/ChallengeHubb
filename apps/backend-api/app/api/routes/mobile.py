from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import logging
import re
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_mobile_user
from app.core.config import settings
from app.infrastructure.db import (
    AdVideoORM,
    ChallengeParticipationORM,
    MobileTokenORM,
    MobileUserORM,
    ModerationVideoORM,
    NotificationORM,
    PromoCodeORM,
    ReportTicketORM,
    SponsoredChallengeORM,
    SystemSettingsORM,
    IntegrationStateORM,
    UserBadgeORM,
    UserChallengeORM,
    UserFollowORM,
    UserIntegrationORM,
    VideoCommentORM,
    VideoCommentLikeORM,
    VideoLikeORM,
    get_db,
    now_utc,
    to_dict,
)
from app.schemas.mobile import (
    BadgeResponse,
    AssistantRequest,
    AssistantResponse,
    ChallengeParticipationResponse,
    CommentResponse,
    CreateCommentRequest,
    CreateMobileChallengeRequest,
    FcmTokenRequest,
    GoogleLoginRequest,
    IntegrationConnectResponse,
    IntegrationStatusResponse,
    JoinChallengeRequest,
    LeaderboardEntryResponse,
    MobileChallengeResponse,
    MobileLoginRequest,
    MobileRegisterRequest,
    MobileTokenResponse,
    MobileUserResponse,
    MobileVideoResponse,
    NotificationResponse,
    PinBadgesRequest,
    PremiumCheckoutResponse,
    PublicProfileResponse,
    ReportVideoRequest,
    UpdateMobileProfileRequest,
    VideoExportResponse,
)

router = APIRouter(prefix="/mobile", tags=["mobile"])
logger = logging.getLogger("challengehub.api")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _mobile_user_response(user: MobileUserORM) -> MobileUserResponse:
    return MobileUserResponse(**to_dict(user))


def _video_response(video: ModerationVideoORM, db: Session, current_user_id: str | None = None) -> MobileVideoResponse:
    data = to_dict(video)
    data["is_ad"] = False
    likes_count = db.scalar(select(func.count(VideoLikeORM.id)).where(VideoLikeORM.video_id == video.id)) or 0
    comments_count = db.scalar(select(func.count(VideoCommentORM.id)).where(VideoCommentORM.video_id == video.id)) or 0
    liked_by_me = False
    if current_user_id:
        liked_by_me = (
            db.query(VideoLikeORM)
            .filter(VideoLikeORM.video_id == video.id, VideoLikeORM.user_id == current_user_id)
            .first()
            is not None
        )
    data["likes_count"] = int(likes_count)
    data["comments_count"] = int(comments_count)
    data["liked_by_me"] = liked_by_me
    author = db.get(MobileUserORM, video.author_user_id)
    if author:
        data["author_display_name"] = author.full_name
        data["author_username"] = author.username
        data["author_avatar_url"] = author.avatar_url
    challenge = db.get(SponsoredChallengeORM, video.challenge_id) if video.challenge_type == "SPONSORED" else db.get(UserChallengeORM, video.challenge_id)
    if challenge:
        data["challenge_title"] = challenge.title
        data["challenge_xp_reward"] = challenge.xp_reward
    return MobileVideoResponse(**data)


def _ad_video_response(ad: AdVideoORM) -> MobileVideoResponse:
    return MobileVideoResponse(
        id=ad.id,
        challenge_id="ad_catalog",
        challenge_type="AD",
        author_user_id=ad.created_by_admin_id or "system",
        url=ad.file_path or ad.url or "",
        description=ad.description,
        ai_status="APPROVED",
        status=ad.status,
        reports_count=0,
        is_ad=True,
        views_count=ad.views_count,
        likes_count=0,
        shares_count=ad.shares_count,
        created_at=ad.created_at.isoformat() if ad.created_at else _utc_now().isoformat(),
        liked_by_me=False,
        comments_count=0,
        author_display_name="Реклама",
        author_username="ad",
        author_avatar_url=None,
        challenge_title="Рекламне відео",
        challenge_xp_reward=None,
    )


def _mobile_user_id_from_header(authorization: str | None, db: Session) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    row = db.get(MobileTokenORM, token)
    return row.user_id if row else None


def _challenge_response(
    row: SponsoredChallengeORM | UserChallengeORM,
    challenge_type: str,
    db: Session,
    creator_name: str | None = None,
    participation: ChallengeParticipationORM | None = None,
) -> MobileChallengeResponse:
    data = to_dict(row)
    data["challenge_type"] = challenge_type
    data["creator_name"] = creator_name
    data["participants_count"] = int(
        db.scalar(
            select(func.count(ChallengeParticipationORM.id)).where(
                ChallengeParticipationORM.challenge_id == row.id,
                ChallengeParticipationORM.challenge_type == challenge_type,
                ChallengeParticipationORM.status.in_(["ACTIVE", "COMPLETED"]),
            )
        )
        or 0
    )
    if participation:
        data["participation_status"] = participation.status
        data["started_at"] = participation.started_at.isoformat() if participation.started_at else None
        data["completed_at"] = participation.completed_at.isoformat() if participation.completed_at else None
        data["progress_videos"] = int(
            db.scalar(
                select(func.count(ModerationVideoORM.id)).where(
                    ModerationVideoORM.author_user_id == participation.user_id,
                    ModerationVideoORM.challenge_id == row.id,
                    ModerationVideoORM.challenge_type == challenge_type,
                    ModerationVideoORM.status == "PUBLISHED",
                )
            )
            or 0
        )
    else:
        data["progress_videos"] = 0
    return MobileChallengeResponse(**data)


def _public_profile_response(user: MobileUserORM, db: Session, viewer_id: str | None = None) -> PublicProfileResponse:
    badges = db.execute(select(UserBadgeORM).where(UserBadgeORM.user_id == user.id)).scalars().all()
    videos = db.execute(
        select(ModerationVideoORM)
        .where(ModerationVideoORM.author_user_id == user.id, ModerationVideoORM.status == "PUBLISHED")
        .order_by(ModerationVideoORM.created_at.desc())
    ).scalars().all()
    participations = db.execute(
        select(ChallengeParticipationORM)
        .where(ChallengeParticipationORM.user_id == user.id, ChallengeParticipationORM.status.in_(["ACTIVE", "COMPLETED"]))
        .order_by(ChallengeParticipationORM.started_at.desc())
    ).scalars().all()
    creators = {u.id: u.full_name for u in db.execute(select(MobileUserORM)).scalars().all()}
    challenges: list[MobileChallengeResponse] = []
    for participation in participations:
        if participation.challenge_type == "SPONSORED":
            challenge = db.get(SponsoredChallengeORM, participation.challenge_id)
            if challenge:
                challenges.append(_challenge_response(challenge, "SPONSORED", db, participation=participation))
        else:
            challenge = db.get(UserChallengeORM, participation.challenge_id)
            if challenge:
                challenges.append(_challenge_response(challenge, "USER", db, creators.get(challenge.created_by_user_id), participation))
    followers_count = db.scalar(select(func.count(UserFollowORM.id)).where(UserFollowORM.followed_id == user.id)) or 0
    following_count = db.scalar(select(func.count(UserFollowORM.id)).where(UserFollowORM.follower_id == user.id)) or 0
    is_following = False
    if viewer_id and viewer_id != user.id:
        is_following = db.query(UserFollowORM).filter(UserFollowORM.follower_id == viewer_id, UserFollowORM.followed_id == user.id).first() is not None
    return PublicProfileResponse(
        user=_mobile_user_response(user),
        badges=[BadgeResponse(**to_dict(row)) for row in badges],
        videos=[_video_response(row, db, viewer_id) for row in videos],
        challenges=challenges,
        followers_count=int(followers_count),
        following_count=int(following_count),
        is_following=is_following,
    )


BADGE_CATALOG = {
    "first_video": ("Перший челендж", "Опублікувати перше відео-звіт."),
    "weekly_warrior": ("Воїн тижня", "Завершити 3 челенджі."),
    "social_butterfly": ("Соціальний метелик", "Отримати 10 лайків на свої відео."),
    "creative_mind": ("Творчий розум", "Створити 5 власних челенджів."),
    "xp_hunter": ("Мисливець за XP", "Набрати 1000 XP."),
    "premium_star": ("Premium-зірка", "Активувати ChallengeHub Premium."),
}


def _grant_badge(db: Session, user_id: str, badge_code: str) -> None:
    if badge_code not in BADGE_CATALOG:
        return
    exists = (
        db.query(UserBadgeORM)
        .filter(UserBadgeORM.user_id == user_id, UserBadgeORM.badge_code == badge_code)
        .first()
    )
    if exists:
        return
    title, description = BADGE_CATALOG[badge_code]
    db.add(
        UserBadgeORM(
            id=f"badge_{uuid4().hex[:10]}",
            user_id=user_id,
            badge_code=badge_code,
            title=title,
            description=description,
            is_pinned=False,
        )
    )


def _refresh_user_badges(db: Session, user: MobileUserORM) -> None:
    videos_count = db.query(ModerationVideoORM).filter(ModerationVideoORM.author_user_id == user.id).count()
    completed_count = (
        db.query(ChallengeParticipationORM)
        .filter(ChallengeParticipationORM.user_id == user.id, ChallengeParticipationORM.status == "COMPLETED")
        .count()
    )
    created_count = db.query(UserChallengeORM).filter(UserChallengeORM.created_by_user_id == user.id).count()
    likes_received = (
        db.query(func.count(VideoLikeORM.id))
        .join(ModerationVideoORM, ModerationVideoORM.id == VideoLikeORM.video_id)
        .filter(ModerationVideoORM.author_user_id == user.id)
        .scalar()
        or 0
    )
    if videos_count >= 1:
        _grant_badge(db, user.id, "first_video")
    if completed_count >= 3:
        _grant_badge(db, user.id, "weekly_warrior")
    if likes_received >= 10:
        _grant_badge(db, user.id, "social_butterfly")
    if created_count >= 5:
        _grant_badge(db, user.id, "creative_mind")
    if user.xp >= 1000:
        _grant_badge(db, user.id, "xp_hunter")
    if user.is_premium:
        _grant_badge(db, user.id, "premium_star")


def _issue_mobile_token(user: MobileUserORM, db: Session) -> MobileTokenResponse:
    user.last_active_at = now_utc()
    token = f"mobile_{uuid4().hex}"
    db.add(MobileTokenORM(token=token, user_id=user.id))
    db.commit()
    db.refresh(user)
    return MobileTokenResponse(access_token=token, user=_mobile_user_response(user))


def _fallback_assistant_answer(message: str, xp: int, challenge: SponsoredChallengeORM | UserChallengeORM | None) -> str:
    challenge_part = f' Рекомендую почати з челенджу "{challenge.title}".' if challenge else ""
    return (
        f"Ти маєш {xp} XP. Сформулюй коротку ціль на сьогодні, запиши відео до 30 секунд "
        f"і додай зрозумілий опис.{challenge_part} "
        f'За твоїм запитом "{message}" найкраща дія зараз: обрати один челендж, виконати його без відкладання '
        "і не гнатися за ідеальним результатом."
    )


def _challenge_participants_count(db: Session, challenge_id: str, challenge_type: str) -> int:
    return int(
        db.execute(
            select(func.count(ChallengeParticipationORM.id)).where(
                ChallengeParticipationORM.challenge_id == challenge_id,
                ChallengeParticipationORM.challenge_type == challenge_type,
                ChallengeParticipationORM.status.in_(["ACTIVE", "COMPLETED"]),
            )
        ).scalar_one()
        or 0
    )


def _challenge_context_row(db: Session, row: SponsoredChallengeORM | UserChallengeORM, challenge_type: str) -> dict[str, object]:
    return {
        "id": row.id,
        "type": challenge_type,
        "title": row.title,
        "description": row.description,
        "difficulty": row.difficulty,
        "duration_days": row.duration_days,
        "xp_reward": row.xp_reward,
        "participants_count": _challenge_participants_count(db, row.id, challenge_type),
    }


def _assistant_context(db: Session, user: MobileUserORM) -> tuple[dict[str, object], SponsoredChallengeORM | UserChallengeORM | None]:
    badges = db.execute(
        select(UserBadgeORM)
        .where(UserBadgeORM.user_id == user.id)
        .order_by(UserBadgeORM.created_at.desc())
    ).scalars().all()
    participations = db.execute(
        select(ChallengeParticipationORM)
        .where(ChallengeParticipationORM.user_id == user.id)
        .order_by(ChallengeParticipationORM.started_at.desc())
    ).scalars().all()
    sponsored = db.execute(
        select(SponsoredChallengeORM)
        .where(SponsoredChallengeORM.status == "PUBLISHED")
        .order_by(SponsoredChallengeORM.xp_reward.desc(), SponsoredChallengeORM.published_at.desc(), SponsoredChallengeORM.created_at.desc())
        .limit(40)
    ).scalars().all()
    regular = db.execute(
        select(UserChallengeORM)
        .where(UserChallengeORM.status == "PUBLISHED")
        .order_by(UserChallengeORM.xp_reward.desc(), UserChallengeORM.created_at.desc())
        .limit(40)
    ).scalars().all()

    challenge_by_key: dict[tuple[str, str], SponsoredChallengeORM | UserChallengeORM] = {}
    challenge_by_key.update({("SPONSORED", row.id): row for row in sponsored})
    challenge_by_key.update({("USER", row.id): row for row in regular})

    participation_context = []
    for item in participations[:20]:
        challenge = challenge_by_key.get((item.challenge_type, item.challenge_id))
        if not challenge:
            challenge = db.get(SponsoredChallengeORM, item.challenge_id) if item.challenge_type == "SPONSORED" else db.get(UserChallengeORM, item.challenge_id)
        participation_context.append(
            {
                "challenge_id": item.challenge_id,
                "challenge_type": item.challenge_type,
                "title": challenge.title if challenge else None,
                "status": item.status,
                "started_at": item.started_at.isoformat() if item.started_at else None,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            }
        )

    challenges = [_challenge_context_row(db, row, "SPONSORED") for row in sponsored]
    challenges += [_challenge_context_row(db, row, "USER") for row in regular]
    suggested = next(iter(sponsored), None) or next(iter(regular), None)
    context = {
        "app_capabilities": {
            "auth": ["email_login", "google_login"],
            "feed": ["short_videos", "likes", "comments", "shares", "report_video"],
            "challenges": [
                "view_challenges",
                "join_leave_challenge",
                "challenge_details",
                "create_user_challenge",
                "upload_video_to_challenge",
            ],
            "profile": [
                "view_own_and_public_profiles",
                "follow_unfollow_users",
                "edit_profile_name_username_avatar",
                "pin_up_to_3_badges",
                "profile_background_for_premium",
            ],
            "integrations": ["connect_youtube", "connect_tiktok", "export_video_after_publish"],
            "premium": ["2x_xp_boost", "no_feed_ads", "ai_assistant_access"],
            "assistant": ["challenge_recommendations", "feature_help", "motivation_and_plans"],
            "moderation": ["ai_precheck", "manual_queue_for_flagged_content"],
            "notifications": ["in_app_notifications", "inactivity_comeback_reminders"],
        },
        "feature_rules": {
            "ai_assistant_requires_premium": True,
            "video_upload_requires_selected_challenge": True,
            "max_pinned_badges": 3,
            "premium_backgrounds_only_for_premium": True,
        },
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "xp": user.xp,
            "level": (user.xp // 1000) + 1,
            "is_premium": user.is_premium,
            "status": user.status,
        },
        "badges": [
            {
                "code": badge.badge_code,
                "title": badge.title,
                "description": badge.description,
                "is_pinned": badge.is_pinned,
                "earned_at": badge.created_at.isoformat() if badge.created_at else None,
            }
            for badge in badges
        ],
        "participations": participation_context,
        "available_challenges": challenges,
        "ranking_hint": "Для топу челенджів враховуй xp_reward, participants_count, difficulty і duration_days. Не вигадуй челенджі поза available_challenges.",
    }
    return context, suggested


def _call_gemini_assistant(message: str, user: MobileUserORM, db: Session) -> tuple[str, str | None]:
    context, suggested_challenge = _assistant_context(db, user)
    suggested_id = suggested_challenge.id if suggested_challenge else None
    if not settings.gemini_api_key:
        return _fallback_assistant_answer(message, user.xp, suggested_challenge), suggested_id

    system_prompt = """
Ти AI-помічник мобільного застосунку ChallengeHub.
Відповідай українською мовою, коротко, конкретно і дружньо.
Ти бачиш реальний контекст користувача: XP, рівень, premium-статус, отримані значки, участі в челенджах і доступні челенджі.
Можеш радити топ челенджів, пояснювати як отримати XP/значки, пропонувати ідеї для відео, а також пояснювати функціонал застосунку:
що натиснути, де знайти потрібну функцію, які є обмеження і що доступно тільки для Premium.
Орієнтуйся на app_capabilities та feature_rules в контексті; якщо функції немає в app_capabilities — прямо скажи, що вона не підтримується.
Не вигадуй неіснуючі значки, челенджі, нагороди або статистику. Якщо даних бракує, прямо скажи це і запропонуй практичний наступний крок.
Не давай небезпечних, образливих, незаконних або медичних/фінансових інструкцій.
Формат відповіді: 2-5 речень або короткий список до 4 пунктів.
""".strip()
    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Контекст ChallengeHub:\n"
                            f"{json.dumps(context, ensure_ascii=False)}\n\n"
                            f"Запит користувача: {message}"
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 900,
        },
    }
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        candidate = payload["candidates"][0]
        parts = candidate["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
        finish_reason = str(candidate.get("finishReason") or "")
        if finish_reason == "MAX_TOKENS" and text and text[-1] not in ".!?":
            text = f"{text}..."
        return text or _fallback_assistant_answer(message, user.xp, suggested_challenge), suggested_id
    except Exception:
        return _fallback_assistant_answer(message, user.xp, suggested_challenge), suggested_id


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _moderate_video_with_gemini(
    *,
    video_description: str | None,
    threshold: float,
) -> tuple[str, str, str | None, float | None]:
    if not settings.gemini_api_key:
        return "REJECTED", "PENDING_MANUAL", "Gemini API key is missing", None

    prompt = (
        "You are a strict challenge-video moderation classifier.\n"
        "Analyze TEXT ONLY (video description and metadata).\n"
        "Return ONLY JSON: {\"decision\":\"APPROVE|REJECT\",\"reject_confidence\":0..1,\"reason\":\"...\"}.\n"
        "Reject if description indicates profanity, hate speech, harassment, explicit violence, illegal activity promotion, or obvious advertising/spam.\n"
        "If uncertain, prefer REJECT with moderate confidence.\n"
        f"video_description: {video_description or ''}\n"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.9,
            "maxOutputTokens": 300,
            "responseMimeType": "application/json",
        },
    }
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        parts = payload["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
        data = _extract_json_object(text) or {}
        decision = str(data.get("decision", "APPROVE")).upper()
        try:
            reject_confidence = float(data.get("reject_confidence", 0.0))
        except Exception:
            reject_confidence = 0.0
        reject_confidence = max(0.0, min(1.0, reject_confidence))
        reason = str(data.get("reason") or "").strip() or None
        logger.info(
            "AI moderation result: decision=%s reject_confidence=%.3f threshold=%.3f reason=%s description=%s prompt=%s result=%s",
            decision,
            reject_confidence,
            threshold,
            reason or "-",
            video_description or "-",
            prompt.replace("\n", "\\n"),
            text,
        )
        if decision == "REJECT" and reject_confidence >= threshold:
            return "REJECTED", "PENDING_MANUAL", reason, reject_confidence
        return "APPROVED", "PUBLISHED", reason, reject_confidence
    except Exception as exc:
        logger.exception("AI moderation failed, fallback to manual moderation: %s", exc)
        return "REJECTED", "PENDING_MANUAL", "AI moderation unavailable, routed to manual review", None


def _youtube_oauth_configured() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret and settings.youtube_redirect_url)


def _youtube_token_request(payload: dict[str, str]) -> dict[str, object]:
    request = Request(
        "https://oauth2.googleapis.com/token",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = _read_google_http_error(exc, "Google OAuth token request failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc


def _as_naive_utc(value):
    return value.replace(tzinfo=None) if getattr(value, "tzinfo", None) else value


def _refresh_youtube_access_token(db: Session, integration: UserIntegrationORM) -> str:
    expires_at = _as_naive_utc(integration.token_expires_at) if integration.token_expires_at else None
    refresh_deadline = _as_naive_utc(now_utc() + timedelta(seconds=60))
    if integration.access_token and expires_at and expires_at > refresh_deadline:
        return integration.access_token
    if not integration.refresh_token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="YouTube account must be connected again")
    data = _youtube_token_request(
        {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": integration.refresh_token,
            "grant_type": "refresh_token",
        }
    )
    integration.access_token = str(data["access_token"])
    integration.token_expires_at = now_utc() + timedelta(seconds=int(data.get("expires_in", 3600)))
    integration.updated_at = now_utc()
    db.commit()
    return integration.access_token


def _youtube_upload(access_token: str, video: ModerationVideoORM, db: Session) -> str:
    path = Path(video.url)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file is not available on backend storage")
    challenge_title = ""
    if video.challenge_type == "SPONSORED":
        challenge = db.get(SponsoredChallengeORM, video.challenge_id)
    else:
        challenge = db.get(UserChallengeORM, video.challenge_id)
    if challenge and getattr(challenge, "title", None):
        challenge_title = str(challenge.title)
    tag_parts = re.findall(r"[A-Za-z0-9]+", challenge_title)
    challenge_tag = f"#{''.join(part.capitalize() for part in tag_parts)[:40]}" if tag_parts else ""
    tags = "#ChallengeHub" + (f" {challenge_tag}" if challenge_tag else "")
    metadata = {
        "snippet": {
            "title": f"ChallengeHub Shorts: {video.description or video.id}"[:100],
            "description": f"{video.description or ''}\n\nОпубліковано з ChallengeHub {tags}",
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "unlisted",
            "selfDeclaredMadeForKids": False,
        },
    }
    boundary = f"challengehub_{uuid4().hex}"
    file_bytes = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata, ensure_ascii=False)}\r\n"
        f"--{boundary}\r\n"
        "Content-Type: video/mp4\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    request = Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=multipart",
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = _read_google_http_error(exc, "YouTube upload failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
    youtube_id = payload.get("id")
    if not youtube_id:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="YouTube upload did not return video id")
    return f"https://youtube.com/shorts/{youtube_id}"


def _tiktok_oauth_configured() -> bool:
    return bool(settings.tiktok_client_key and settings.tiktok_client_secret and settings.tiktok_redirect_url)


def _tiktok_token_request(payload: dict[str, str]) -> dict[str, object]:
    request = Request(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _tiktok_error_detail(payload: dict[str, object], fallback: str) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        code = str(error.get("code") or "").strip()
        message = str(error.get("message") or "").strip()
        log_id = str(error.get("log_id") or error.get("logid") or "").strip()
        parts = [part for part in [code, message, f"log_id={log_id}" if log_id else ""] if part]
        if parts and code != "ok":
            return f"{fallback}: {'; '.join(parts)}"
    return fallback


def _google_error_detail(payload: dict[str, object], fallback: str) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = str(error.get("message") or "").strip()
        code = str(error.get("code") or "").strip()
        status_text = str(error.get("status") or "").strip()
        details = error.get("errors")
        reason = ""
        if isinstance(details, list) and details:
            first = details[0]
            if isinstance(first, dict):
                reason = str(first.get("reason") or "").strip()
        parts = [p for p in [message, f"reason={reason}" if reason else "", f"status={status_text}" if status_text else "", f"code={code}" if code else ""] if p]
        if parts:
            return f"{fallback}: {'; '.join(parts)}"
    if isinstance(error, str) and error.strip():
        return f"{fallback}: {error.strip()}"
    return fallback


def _read_tiktok_http_error(error: HTTPError, fallback: str) -> str:
    try:
        body = error.read().decode("utf-8")
        payload = json.loads(body)
        return _tiktok_error_detail(payload, f"{fallback}: HTTP {error.code}")
    except Exception:
        return f"{fallback}: HTTP {error.code}"


def _read_google_http_error(error: HTTPError, fallback: str) -> str:
    try:
        body = error.read().decode("utf-8")
        payload = json.loads(body)
        return _google_error_detail(payload, f"{fallback}: HTTP {error.code}")
    except Exception:
        return f"{fallback}: HTTP {error.code}"


def _refresh_tiktok_access_token(db: Session, integration: UserIntegrationORM) -> str:
    expires_at = _as_naive_utc(integration.token_expires_at) if integration.token_expires_at else None
    refresh_deadline = _as_naive_utc(now_utc() + timedelta(seconds=60))
    if integration.access_token and expires_at and expires_at > refresh_deadline:
        return integration.access_token
    if not integration.refresh_token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TikTok account must be connected again")
    data = _tiktok_token_request(
        {
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "refresh_token": integration.refresh_token,
            "grant_type": "refresh_token",
        }
    )
    integration.access_token = str(data["access_token"])
    integration.token_expires_at = now_utc() + timedelta(seconds=int(data.get("expires_in", 3600)))
    if data.get("refresh_token"):
        integration.refresh_token = str(data["refresh_token"])
    integration.updated_at = now_utc()
    db.commit()
    return integration.access_token


def _tiktok_account_name(access_token: str) -> str:
    request = Request(
        "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name",
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("data", {}).get("user", {}).get("display_name") or "TikTok"
    except Exception:
        return "TikTok"


def _tiktok_upload(access_token: str, video: ModerationVideoORM) -> str:
    path = Path(video.url)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file is not available on backend storage")
    file_size = path.stat().st_size
    init_body = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }
    init_request = Request(
        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        data=json.dumps(init_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urlopen(init_request, timeout=30) as response:
            init_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_read_tiktok_http_error(exc, "TikTok upload init failed")) from exc
    error_detail = _tiktok_error_detail(init_payload, "TikTok upload init failed")
    if error_detail != "TikTok upload init failed":
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=error_detail)
    data = init_payload.get("data") or {}
    upload_url = data.get("upload_url")
    publish_id = data.get("publish_id")
    if not upload_url or not publish_id:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="TikTok upload init failed")
    file_bytes = path.read_bytes()
    upload_request = Request(
        upload_url,
        data=file_bytes,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        },
        method="PUT",
    )
    try:
        with urlopen(upload_request, timeout=90):
            pass
    except HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_read_tiktok_http_error(exc, "TikTok file upload failed")) from exc
    return f"tiktok_publish_id:{publish_id}"


@router.post("/auth/register", response_model=MobileTokenResponse)
def register_mobile_user(payload: MobileRegisterRequest, db: Session = Depends(get_db)) -> MobileTokenResponse:
    existing = db.execute(
        select(MobileUserORM).where((MobileUserORM.email == payload.email) | (MobileUserORM.username == payload.username))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists")
    user = MobileUserORM(
        id=f"mu_{uuid4().hex[:10]}",
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        auth_provider="password",
        xp=0,
        is_premium=False,
        status="ACTIVE",
        last_active_at=now_utc(),
    )
    token = f"mobile_{uuid4().hex}"
    try:
        db.add(user)
        db.flush()  # ensure mobile_users row exists before FK insert into mobile_auth_tokens
        db.add(MobileTokenORM(token=token, user_id=user.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists") from exc
    db.refresh(user)
    return MobileTokenResponse(access_token=token, user=_mobile_user_response(user))


@router.post("/auth/login", response_model=MobileTokenResponse)
def login_mobile_user(payload: MobileLoginRequest, db: Session = Depends(get_db)) -> MobileTokenResponse:
    user = db.execute(select(MobileUserORM).where(MobileUserORM.email == payload.email)).scalar_one_or_none()
    if not user or user.password != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _issue_mobile_token(user, db)


@router.post("/auth/google", response_model=MobileTokenResponse)
def google_mobile_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> MobileTokenResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={quote(payload.id_token)}"
    try:
        with urlopen(url, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token") from exc
    if data.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google token audience mismatch")
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account email is missing")
    user = db.execute(select(MobileUserORM).where(MobileUserORM.email == email)).scalar_one_or_none()
    if not user:
        name = data.get("name") or email.split("@")[0]
        base_username = f"g_{email.split('@')[0]}".replace(".", "_")[:58]
        username = base_username
        suffix = 1
        while db.execute(select(MobileUserORM).where(MobileUserORM.username == username)).scalar_one_or_none():
            username = f"{base_username}_{suffix}"[:64]
            suffix += 1
        user = MobileUserORM(
            id=f"mu_{uuid4().hex[:10]}",
            username=username,
            full_name=name,
            email=email,
            password="GOOGLE_OAUTH",
            auth_provider="google",
            avatar_url=data.get("picture"),
            xp=0,
            is_premium=False,
            status="ACTIVE",
            last_active_at=now_utc(),
        )
        db.add(user)
        db.flush()
    else:
        user.auth_provider = "google" if user.password == "GOOGLE_OAUTH" else user.auth_provider
        if data.get("picture") and not user.avatar_url:
            user.avatar_url = data.get("picture")
    return _issue_mobile_token(user, db)


@router.get("/auth/me", response_model=MobileUserResponse)
def mobile_me(current_user: MobileUserResponse = Depends(get_current_mobile_user)) -> MobileUserResponse:
    return current_user


@router.get("/users/{user_id}/profile", response_model=PublicProfileResponse)
def get_public_profile(
    user_id: str,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> PublicProfileResponse:
    user = db.get(MobileUserORM, user_id)
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    viewer_id = _mobile_user_id_from_header(authorization, db)
    return _public_profile_response(user, db, viewer_id)


@router.post("/users/{user_id}/follow", response_model=PublicProfileResponse)
def follow_user(
    user_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> PublicProfileResponse:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
    user = db.get(MobileUserORM, user_id)
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = db.query(UserFollowORM).filter(UserFollowORM.follower_id == current_user.id, UserFollowORM.followed_id == user_id).first()
    if not existing:
        db.add(UserFollowORM(id=f"uf_{uuid4().hex[:10]}", follower_id=current_user.id, followed_id=user_id))
        db.commit()
    return _public_profile_response(user, db, current_user.id)


@router.delete("/users/{user_id}/follow", response_model=PublicProfileResponse)
def unfollow_user(
    user_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> PublicProfileResponse:
    user = db.get(MobileUserORM, user_id)
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = db.query(UserFollowORM).filter(UserFollowORM.follower_id == current_user.id, UserFollowORM.followed_id == user_id).first()
    if existing:
        db.delete(existing)
        db.commit()
    return _public_profile_response(user, db, current_user.id)


@router.get("/feed", response_model=list[MobileVideoResponse])
def get_feed(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> list[MobileVideoResponse]:
    current_user_id = _mobile_user_id_from_header(authorization, db)
    current_user = db.get(MobileUserORM, current_user_id) if current_user_id else None
    videos = (
        db.execute(select(ModerationVideoORM).where(ModerationVideoORM.status == "PUBLISHED").order_by(ModerationVideoORM.created_at.desc()))
        .scalars()
        .all()
    )
    if current_user and current_user.is_premium:
        return [_video_response(video, db, current_user_id) for video in videos]

    ads = (
        db.execute(select(AdVideoORM).where(AdVideoORM.status == "PUBLISHED").order_by(AdVideoORM.created_at.desc()))
        .scalars()
        .all()
    )
    if not ads:
        return [_video_response(video, db, current_user_id) for video in videos]

    mixed: list[MobileVideoResponse] = []
    ad_index = 0
    for idx, item in enumerate(videos, start=1):
        mixed.append(_video_response(item, db, current_user_id))
        if idx % 4 == 0 and ad_index < len(ads):
            mixed.append(_ad_video_response(ads[ad_index]))
            ad_index += 1
    if not videos:
        mixed.extend(_ad_video_response(ad) for ad in ads[:3])
    return mixed


@router.get("/challenges", response_model=list[MobileChallengeResponse])
def list_mobile_challenges(db: Session = Depends(get_db)) -> list[MobileChallengeResponse]:
    sponsored = db.execute(select(SponsoredChallengeORM).where(SponsoredChallengeORM.status == "PUBLISHED")).scalars().all()
    regular = db.execute(select(UserChallengeORM).where(UserChallengeORM.status == "PUBLISHED")).scalars().all()
    creators = {u.id: u.full_name for u in db.execute(select(MobileUserORM)).scalars().all()}
    result = [_challenge_response(item, "SPONSORED", db) for item in sponsored]
    result.extend(_challenge_response(item, "USER", db, creators.get(item.created_by_user_id)) for item in regular)
    return result


@router.post("/challenges", response_model=MobileChallengeResponse)
def create_mobile_challenge(
    payload: CreateMobileChallengeRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> MobileChallengeResponse:
    if payload.difficulty not in {"easy", "normal", "hard"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported difficulty")
    challenge = UserChallengeORM(
        id=f"uc_{uuid4().hex[:10]}",
        title=payload.title,
        description=payload.description,
        difficulty=payload.difficulty,
        duration_days=payload.duration_days,
        xp_reward=min(payload.xp_reward, 500),
        created_by_user_id=current_user.id,
        status="PUBLISHED",
    )
    db.add(challenge)
    user = db.get(MobileUserORM, current_user.id)
    if user:
        _refresh_user_badges(db, user)
    db.commit()
    db.refresh(challenge)
    return _challenge_response(challenge, "USER", db, current_user.full_name)


@router.post("/challenges/{challenge_id}/join", response_model=ChallengeParticipationResponse)
def join_challenge(
    challenge_id: str,
    payload: JoinChallengeRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> ChallengeParticipationResponse:
    challenge_type = payload.challenge_type
    if challenge_type not in {"SPONSORED", "USER"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported challenge type")
    if challenge_type == "SPONSORED":
        challenge_exists = db.get(SponsoredChallengeORM, challenge_id) is not None
    else:
        challenge_exists = db.get(UserChallengeORM, challenge_id) is not None
    if not challenge_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    active_count = (
        db.query(ChallengeParticipationORM)
        .filter(ChallengeParticipationORM.user_id == current_user.id, ChallengeParticipationORM.status == "ACTIVE")
        .count()
    )
    if active_count >= 5:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active challenge limit reached")
    existing = (
        db.query(ChallengeParticipationORM)
        .filter(
            ChallengeParticipationORM.user_id == current_user.id,
            ChallengeParticipationORM.challenge_id == challenge_id,
            ChallengeParticipationORM.challenge_type == challenge_type,
        )
        .first()
    )
    if existing:
        return ChallengeParticipationResponse(**to_dict(existing))
    row = ChallengeParticipationORM(
        id=f"cp_{uuid4().hex[:10]}",
        user_id=current_user.id,
        challenge_id=challenge_id,
        challenge_type=challenge_type,
        status="ACTIVE",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ChallengeParticipationResponse(**to_dict(row))


@router.post("/challenges/{challenge_id}/leave", response_model=ChallengeParticipationResponse)
def leave_challenge(
    challenge_id: str,
    payload: JoinChallengeRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> ChallengeParticipationResponse:
    row = (
        db.query(ChallengeParticipationORM)
        .filter(
            ChallengeParticipationORM.user_id == current_user.id,
            ChallengeParticipationORM.challenge_id == challenge_id,
            ChallengeParticipationORM.challenge_type == payload.challenge_type,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation not found")
    data = to_dict(row)
    db.delete(row)
    db.commit()
    return ChallengeParticipationResponse(**data)


@router.post("/videos", response_model=MobileVideoResponse)
async def upload_challenge_video(
    challenge_id: str = Form(...),
    challenge_type: str = Form("SPONSORED"),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> MobileVideoResponse:
    if challenge_type not in {"SPONSORED", "USER"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported challenge type")
    challenge = db.get(SponsoredChallengeORM, challenge_id) if challenge_type == "SPONSORED" else db.get(UserChallengeORM, challenge_id)
    if not challenge or challenge.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only published challenges can receive video submissions")
    uploads_dir = Path("uploads/mobile-videos")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    file_name = f"video_{uuid4().hex}{suffix}"
    target = uploads_dir / file_name
    target.write_bytes(await file.read())
    system_settings = db.get(SystemSettingsORM, "settings_main")
    threshold = float(system_settings.ai_confidence_threshold) if system_settings else 0.85
    ai_status, moderation_status, ai_reason, ai_confidence = _moderate_video_with_gemini(
        video_description=description,
        threshold=threshold,
    )
    video = ModerationVideoORM(
        id=f"vid_{uuid4().hex[:10]}",
        challenge_id=challenge_id,
        challenge_type=challenge_type,
        author_user_id=current_user.id,
        url=str(target).replace("\\", "/"),
        description=description,
        ai_reason=ai_reason,
        ai_confidence=ai_confidence,
        ai_status=ai_status,
        status=moderation_status,
        reports_count=0,
    )
    participation = (
        db.query(ChallengeParticipationORM)
        .filter(
            ChallengeParticipationORM.user_id == current_user.id,
            ChallengeParticipationORM.challenge_id == challenge_id,
            ChallengeParticipationORM.challenge_type == challenge_type,
        )
        .first()
    )
    db.add(video)
    db.flush()

    required_videos = max(1, int(challenge.duration_days))
    published_videos_count = int(
        db.scalar(
            select(func.count(ModerationVideoORM.id)).where(
                ModerationVideoORM.author_user_id == current_user.id,
                ModerationVideoORM.challenge_id == challenge_id,
                ModerationVideoORM.challenge_type == challenge_type,
                ModerationVideoORM.status == "PUBLISHED",
            )
        )
        or 0
    )
    reached_completion = published_videos_count >= required_videos

    was_completed_before = participation.status == "COMPLETED" if participation else False
    just_completed = False
    if participation:
        if reached_completion:
            if participation.status != "COMPLETED":
                participation.status = "COMPLETED"
                participation.completed_at = now_utc()
                just_completed = True
        else:
            if participation.status != "COMPLETED":
                participation.status = "ACTIVE"
                participation.completed_at = None
    else:
        just_completed = reached_completion
        db.add(
            ChallengeParticipationORM(
                id=f"cp_{uuid4().hex[:10]}",
                user_id=current_user.id,
                challenge_id=challenge_id,
                challenge_type=challenge_type,
                status="COMPLETED" if reached_completion else "ACTIVE",
                completed_at=now_utc() if reached_completion else None,
            )
        )
    user = db.get(MobileUserORM, current_user.id)
    if user and video.status == "PUBLISHED":
        reward = min(challenge.xp_reward, 2000 if challenge_type == "SPONSORED" else 1000)
        if user.is_premium:
            reward *= 2
        user.xp += reward
        _refresh_user_badges(db, user)
    if challenge_type == "SPONSORED" and just_completed and not was_completed_before:
        promo_text: str | None = None
        if challenge.promo_mode == "SINGLE" and challenge.promo_single_code:
            promo_text = challenge.promo_single_code.strip()
        elif challenge.promo_mode == "LIST":
            promo_row = (
                db.query(PromoCodeORM)
                .filter(PromoCodeORM.challenge_id == challenge_id)
                .first()
            )
            if promo_row and promo_row.code:
                promo_text = promo_row.code.strip()
                db.delete(promo_row)
        if promo_text:
            db.add(
                NotificationORM(
                    id=f"nt_{uuid4().hex[:10]}",
                    user_id=current_user.id,
                    title="Челендж завершено",
                    body=f"Вітаємо! Ваш промокод: {promo_text}",
                )
            )
        else:
            db.add(
                NotificationORM(
                    id=f"nt_{uuid4().hex[:10]}",
                    user_id=current_user.id,
                    title="Челендж завершено",
                    body="Вітаємо! Ви успішно завершили спонсорський челендж.",
                )
            )
    db.commit()
    db.refresh(video)
    return _video_response(video, db, current_user.id)


@router.post("/videos/{video_id}/like", response_model=MobileVideoResponse)
def like_video(
    video_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> MobileVideoResponse:
    video = db.get(ModerationVideoORM, video_id)
    if not video or video.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    existing = db.query(VideoLikeORM).filter(VideoLikeORM.video_id == video_id, VideoLikeORM.user_id == current_user.id).first()
    if not existing:
        db.add(VideoLikeORM(id=f"vl_{uuid4().hex[:10]}", video_id=video_id, user_id=current_user.id))
        author = db.get(MobileUserORM, video.author_user_id)
        if author:
            _refresh_user_badges(db, author)
        db.commit()
        db.refresh(video)
    return _video_response(video, db, current_user.id)


@router.delete("/videos/{video_id}/like", response_model=MobileVideoResponse)
def unlike_video(
    video_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> MobileVideoResponse:
    video = db.get(ModerationVideoORM, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    existing = db.query(VideoLikeORM).filter(VideoLikeORM.video_id == video_id, VideoLikeORM.user_id == current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        db.refresh(video)
    return _video_response(video, db, current_user.id)


@router.get("/videos/{video_id}/comments", response_model=list[CommentResponse])
def list_comments(video_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> list[CommentResponse]:
    current_user_id = _mobile_user_id_from_header(authorization, db)
    comments = db.execute(select(VideoCommentORM).where(VideoCommentORM.video_id == video_id).order_by(VideoCommentORM.created_at.asc())).scalars().all()
    users = {u.id: u for u in db.execute(select(MobileUserORM)).scalars().all()}
    result: list[CommentResponse] = []
    for comment in comments:
        user = users.get(comment.user_id)
        liked_by_me = False
        if current_user_id:
            liked_by_me = db.query(VideoCommentLikeORM).filter(VideoCommentLikeORM.comment_id == comment.id, VideoCommentLikeORM.user_id == current_user_id).first() is not None
        result.append(
            CommentResponse(
                **to_dict(comment),
                username=user.username if user else "unknown",
                display_name=user.full_name if user else None,
                avatar_url=user.avatar_url if user else None,
                liked_by_me=liked_by_me,
            )
        )
    return result


@router.post("/videos/{video_id}/comments", response_model=CommentResponse)
def add_comment(
    video_id: str,
    payload: CreateCommentRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    if not db.get(ModerationVideoORM, video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    comment = VideoCommentORM(id=f"vc_{uuid4().hex[:10]}", video_id=video_id, user_id=current_user.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentResponse(**to_dict(comment), username=current_user.username, display_name=current_user.full_name, avatar_url=current_user.avatar_url)


@router.post("/comments/{comment_id}/like", response_model=CommentResponse)
def like_comment(
    comment_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    comment = db.get(VideoCommentORM, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    existing = db.query(VideoCommentLikeORM).filter(VideoCommentLikeORM.comment_id == comment_id, VideoCommentLikeORM.user_id == current_user.id).first()
    if not existing:
        db.add(VideoCommentLikeORM(id=f"vcl_{uuid4().hex[:10]}", comment_id=comment_id, user_id=current_user.id))
        comment.likes_count += 1
        db.commit()
        db.refresh(comment)
    author = db.get(MobileUserORM, comment.user_id)
    return CommentResponse(**to_dict(comment), username=author.username if author else "unknown", display_name=author.full_name if author else None, avatar_url=author.avatar_url if author else None, liked_by_me=True)


@router.delete("/comments/{comment_id}/like", response_model=CommentResponse)
def unlike_comment(
    comment_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    comment = db.get(VideoCommentORM, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    existing = db.query(VideoCommentLikeORM).filter(VideoCommentLikeORM.comment_id == comment_id, VideoCommentLikeORM.user_id == current_user.id).first()
    if existing:
        db.delete(existing)
        comment.likes_count = max(0, comment.likes_count - 1)
        db.commit()
        db.refresh(comment)
    author = db.get(MobileUserORM, comment.user_id)
    return CommentResponse(**to_dict(comment), username=author.username if author else "unknown", display_name=author.full_name if author else None, avatar_url=author.avatar_url if author else None, liked_by_me=False)


@router.post("/videos/{video_id}/report")
def report_video(
    video_id: str,
    payload: ReportVideoRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    video = db.get(ModerationVideoORM, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    previous_reports = video.reports_count
    video.reports_count += 1
    settings = db.get(SystemSettingsORM, "settings_main")
    if settings and previous_reports < settings.report_limit <= video.reports_count:
        video.status = "PENDING_MANUAL"
    db.add(ReportTicketORM(id=f"rep_{uuid4().hex[:10]}", video_id=video_id, reason=payload.reason, status="OPEN"))
    db.add(NotificationORM(id=f"nt_{uuid4().hex[:10]}", user_id=current_user.id, title="Скаргу прийнято", body="Модератори перевірять відео."))
    db.commit()
    return {"ok": True}


@router.post("/videos/{video_id}/share")
def share_video(
    video_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    video = db.get(ModerationVideoORM, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    video.shares_count += 1
    db.commit()
    return {"ok": True}


@router.post("/videos/{video_id}/view")
def view_video(video_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    video = db.get(ModerationVideoORM, video_id)
    if not video or video.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    video.views_count += 1
    db.commit()
    return {"ok": True}


@router.get("/integrations/youtube/status", response_model=IntegrationStatusResponse)
def youtube_status(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> IntegrationStatusResponse:
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == current_user.id, UserIntegrationORM.provider == "youtube")
    ).scalar_one_or_none()
    return IntegrationStatusResponse(
        provider="youtube",
        connected=bool(integration and integration.refresh_token),
        external_account_name=integration.external_account_name if integration else None,
    )


@router.post("/integrations/youtube/connect-url", response_model=IntegrationConnectResponse)
def youtube_connect_url(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> IntegrationConnectResponse:
    if not _youtube_oauth_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="YouTube OAuth is not configured")
    state = f"yt_{uuid4().hex}"
    db.add(IntegrationStateORM(state=state, user_id=current_user.id, provider="youtube"))
    db.commit()
    params = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.youtube_redirect_url,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.upload openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return IntegrationConnectResponse(connect_url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.delete("/integrations/youtube")
def disconnect_youtube(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == current_user.id, UserIntegrationORM.provider == "youtube")
    ).scalar_one_or_none()
    if integration:
        db.delete(integration)
        db.commit()
    return {"ok": True}


@router.get("/integrations/youtube/callback", response_class=HTMLResponse)
def youtube_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> str:
    if error:
        return _premium_page("YouTube не підключено", f"Google повернув помилку: {error}")
    state_row = db.get(IntegrationStateORM, state or "")
    if not code or not state_row or state_row.provider != "youtube":
        return _premium_page("YouTube не підключено", "OAuth-сесію не знайдено або вона застаріла.")
    try:
        token_data = _youtube_token_request(
            {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.youtube_redirect_url,
            }
        )
    except Exception:
        return _premium_page("YouTube не підключено", "Не вдалося отримати OAuth token від Google.")
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == state_row.user_id, UserIntegrationORM.provider == "youtube")
    ).scalar_one_or_none()
    if not integration:
        integration = UserIntegrationORM(id=f"int_{uuid4().hex[:10]}", user_id=state_row.user_id, provider="youtube")
        db.add(integration)
    integration.access_token = str(token_data["access_token"])
    if token_data.get("refresh_token"):
        integration.refresh_token = str(token_data["refresh_token"])
    integration.token_expires_at = now_utc() + timedelta(seconds=int(token_data.get("expires_in", 3600)))
    integration.external_account_name = "YouTube"
    integration.updated_at = now_utc()
    db.delete(state_row)
    db.commit()
    return _premium_page("YouTube підключено", "Тепер можна експортувати відео в YouTube Shorts після публікації.", "challengehub://integrations/youtube/success")


@router.post("/videos/{video_id}/export/youtube", response_model=VideoExportResponse)
def export_video_to_youtube(
    video_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> VideoExportResponse:
    video = db.get(ModerationVideoORM, video_id)
    if not video or video.author_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only published videos can be exported")
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == current_user.id, UserIntegrationORM.provider == "youtube")
    ).scalar_one_or_none()
    if not integration or not integration.refresh_token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="YouTube account is not connected")
    access_token = _refresh_youtube_access_token(db, integration)
    try:
        external_url = _youtube_upload(access_token, video)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="YouTube upload failed") from exc
    return VideoExportResponse(provider="youtube", exported=True, external_url=external_url, message="Відео експортовано в YouTube Shorts")


@router.get("/integrations/tiktok/status", response_model=IntegrationStatusResponse)
def tiktok_status(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> IntegrationStatusResponse:
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == current_user.id, UserIntegrationORM.provider == "tiktok")
    ).scalar_one_or_none()
    return IntegrationStatusResponse(
        provider="tiktok",
        connected=bool(integration and integration.refresh_token),
        external_account_name=integration.external_account_name if integration else None,
    )


@router.post("/integrations/tiktok/connect-url", response_model=IntegrationConnectResponse)
def tiktok_connect_url(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> IntegrationConnectResponse:
    if not _tiktok_oauth_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="TikTok OAuth is not configured")
    state = f"tt_{uuid4().hex}"
    db.add(IntegrationStateORM(state=state, user_id=current_user.id, provider="tiktok"))
    db.commit()
    params = urlencode(
        {
            "client_key": settings.tiktok_client_key,
            "redirect_uri": settings.tiktok_redirect_url,
            "response_type": "code",
            "scope": "user.info.basic,video.upload",
            "state": state,
        }
    )
    return IntegrationConnectResponse(connect_url=f"https://www.tiktok.com/v2/auth/authorize/?{params}")


@router.delete("/integrations/tiktok")
def disconnect_tiktok(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == current_user.id, UserIntegrationORM.provider == "tiktok")
    ).scalar_one_or_none()
    if integration:
        db.delete(integration)
        db.commit()
    return {"ok": True}


@router.get("/integrations/tiktok/callback", response_class=HTMLResponse)
def tiktok_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> str:
    if error:
        return _premium_page("TikTok не підключено", f"TikTok повернув помилку: {error}")
    state_row = db.get(IntegrationStateORM, state or "")
    if not code or not state_row or state_row.provider != "tiktok":
        return _premium_page("TikTok не підключено", "OAuth-сесію не знайдено або вона застаріла.")
    try:
        token_data = _tiktok_token_request(
            {
                "client_key": settings.tiktok_client_key,
                "client_secret": settings.tiktok_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.tiktok_redirect_url,
            }
        )
    except Exception:
        return _premium_page("TikTok не підключено", "Не вдалося отримати OAuth token від TikTok.")
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == state_row.user_id, UserIntegrationORM.provider == "tiktok")
    ).scalar_one_or_none()
    if not integration:
        integration = UserIntegrationORM(id=f"int_{uuid4().hex[:10]}", user_id=state_row.user_id, provider="tiktok")
        db.add(integration)
    integration.access_token = str(token_data["access_token"])
    if token_data.get("refresh_token"):
        integration.refresh_token = str(token_data["refresh_token"])
    integration.token_expires_at = now_utc() + timedelta(seconds=int(token_data.get("expires_in", 3600)))
    integration.external_account_name = _tiktok_account_name(integration.access_token)
    integration.updated_at = now_utc()
    db.delete(state_row)
    db.commit()
    return _premium_page("TikTok підключено", "Тепер можна завантажувати відео в TikTok після публікації.", "challengehub://integrations/tiktok/success")


@router.post("/videos/{video_id}/export/tiktok", response_model=VideoExportResponse)
def export_video_to_tiktok(
    video_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> VideoExportResponse:
    video = db.get(ModerationVideoORM, video_id)
    if not video or video.author_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only published videos can be exported")
    integration = db.execute(
        select(UserIntegrationORM).where(UserIntegrationORM.user_id == current_user.id, UserIntegrationORM.provider == "tiktok")
    ).scalar_one_or_none()
    if not integration or not integration.refresh_token:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TikTok account is not connected")
    access_token = _refresh_tiktok_access_token(db, integration)
    try:
        external_ref = _tiktok_upload(access_token, video)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="TikTok upload failed") from exc
    return VideoExportResponse(provider="tiktok", exported=True, external_url=external_ref, message="Відео завантажено в TikTok. Відкрийте TikTok inbox, щоб завершити публікацію.")


@router.get("/profile/me", response_model=MobileUserResponse)
def get_profile(current_user: MobileUserResponse = Depends(get_current_mobile_user)) -> MobileUserResponse:
    return current_user


@router.patch("/profile/me", response_model=MobileUserResponse)
def update_profile(
    payload: UpdateMobileProfileRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> MobileUserResponse:
    user = db.get(MobileUserORM, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.username is not None:
        normalized_username = payload.username.strip()
        if not normalized_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username cannot be empty")
        existing = db.execute(
            select(MobileUserORM).where(
                MobileUserORM.username == normalized_username,
                MobileUserORM.id != current_user.id,
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user.username = normalized_username
    if payload.full_name is not None:
        full_name = payload.full_name.strip()
        if not full_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Display name cannot be empty")
        user.full_name = full_name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.profile_background is not None:
        allowed_backgrounds = {"background_1", "background_2", "background_3", "background_4", "background_5", "background_6", "background_7"}
        if payload.profile_background and payload.profile_background not in allowed_backgrounds:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported profile background")
        if payload.profile_background and not user.is_premium:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profile backgrounds are available only for Premium users")
        user.profile_background = payload.profile_background or None
    db.commit()
    db.refresh(user)
    return _mobile_user_response(user)


@router.post("/profile/me/avatar", response_model=MobileUserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> MobileUserResponse:
    user = db.get(MobileUserORM, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    uploads_dir = Path("uploads/avatars")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "avatar.jpg").suffix or ".jpg"
    target = uploads_dir / f"avatar_{uuid4().hex}{suffix}"
    target.write_bytes(await file.read())
    user.avatar_url = str(target).replace("\\", "/")
    db.commit()
    db.refresh(user)
    return _mobile_user_response(user)


@router.get("/profile/me/badges", response_model=list[BadgeResponse])
def get_my_badges(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> list[BadgeResponse]:
    user = db.get(MobileUserORM, current_user.id)
    if user:
        _refresh_user_badges(db, user)
        db.commit()
    rows = db.execute(select(UserBadgeORM).where(UserBadgeORM.user_id == current_user.id)).scalars().all()
    for row in rows:
        if row.badge_code in BADGE_CATALOG:
            row.title, row.description = BADGE_CATALOG[row.badge_code]
    return [BadgeResponse(**to_dict(row)) for row in rows]


@router.get("/profile/me/challenges", response_model=list[MobileChallengeResponse])
def get_my_challenges(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> list[MobileChallengeResponse]:
    rows = (
        db.execute(
            select(ChallengeParticipationORM)
            .where(ChallengeParticipationORM.user_id == current_user.id, ChallengeParticipationORM.status.in_(["ACTIVE", "COMPLETED"]))
            .order_by(ChallengeParticipationORM.started_at.desc())
        )
        .scalars()
        .all()
    )
    creators = {u.id: u.full_name for u in db.execute(select(MobileUserORM)).scalars().all()}
    result: list[MobileChallengeResponse] = []
    for participation in rows:
        if participation.challenge_type == "SPONSORED":
            challenge = db.get(SponsoredChallengeORM, participation.challenge_id)
            if challenge:
                result.append(_challenge_response(challenge, "SPONSORED", db, participation=participation))
        else:
            challenge = db.get(UserChallengeORM, participation.challenge_id)
            if challenge:
                result.append(_challenge_response(challenge, "USER", db, creators.get(challenge.created_by_user_id), participation))
    return result


@router.get("/profile/me/videos", response_model=list[MobileVideoResponse])
def get_my_videos(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> list[MobileVideoResponse]:
    rows = db.execute(
        select(ModerationVideoORM)
        .where(ModerationVideoORM.author_user_id == current_user.id)
        .order_by(ModerationVideoORM.created_at.desc())
    ).scalars().all()
    return [_video_response(row, db, current_user.id) for row in rows]


@router.post("/profile/me/pinned-badges", response_model=list[BadgeResponse])
def pin_badges(
    payload: PinBadgesRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> list[BadgeResponse]:
    if len(payload.badge_ids) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only 3 badges can be pinned")
    rows = db.execute(select(UserBadgeORM).where(UserBadgeORM.user_id == current_user.id)).scalars().all()
    selected = set(payload.badge_ids)
    for row in rows:
        row.is_pinned = row.id in selected
    db.commit()
    return [BadgeResponse(**to_dict(row)) for row in rows]


@router.get("/leaderboard", response_model=list[LeaderboardEntryResponse])
def get_leaderboard(period: str = Query("weekly"), db: Session = Depends(get_db)) -> list[LeaderboardEntryResponse]:
    if period not in {"weekly", "all_time"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported leaderboard period")
    users = db.execute(select(MobileUserORM).order_by(MobileUserORM.xp.desc()).limit(50)).scalars().all()
    return [
        LeaderboardEntryResponse(rank=index + 1, user_id=user.id, username=user.username, full_name=user.full_name, avatar_url=user.avatar_url, xp=user.xp)
        for index, user in enumerate(users)
    ]


@router.get("/notifications", response_model=list[NotificationResponse])
def get_notifications(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> list[NotificationResponse]:
    rows = db.execute(select(NotificationORM).where(NotificationORM.user_id == current_user.id).order_by(NotificationORM.created_at.desc())).scalars().all()
    return [NotificationResponse(**to_dict(row)) for row in rows]


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    row = db.get(NotificationORM, notification_id)
    if not row or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if not row.is_read:
        row.is_read = True
        db.commit()
    return {"ok": True}


@router.post("/notifications/fcm-token")
def register_fcm_token(
    payload: FcmTokenRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    user = db.get(MobileUserORM, current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.fcm_token = payload.token
    db.commit()
    return {"ok": True}


@router.post("/notifications/jobs/inactivity-comeback")
def run_inactivity_comeback_job(
    x_job_token: str | None = Header(default=None, alias="X-Job-Token"),
    inactivity_days: int = Query(default=3, ge=1, le=30),
    cooldown_days: int = Query(default=3, ge=1, le=30),
    max_inactive_days: int = Query(default=14, ge=3, le=90),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    if not x_job_token or x_job_token != settings.mobile_jobs_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid job token")

    now = _utc_now()
    inactive_before = now - timedelta(days=inactivity_days)
    max_inactive_before = now - timedelta(days=max_inactive_days)
    title = "Ми сумуємо за вами"

    users = (
        db.execute(
            select(MobileUserORM).where(
                MobileUserORM.status == "ACTIVE",
                MobileUserORM.last_active_at.is_not(None),
                MobileUserORM.last_active_at <= inactive_before,
                MobileUserORM.last_active_at >= max_inactive_before,
            ).limit(limit)
        )
        .scalars()
        .all()
    )
    if not users:
        return {"checked": 0, "created": 0}

    created = 0
    for user in users:
        if user.last_comeback_notified_at:
            next_allowed = user.last_comeback_notified_at + timedelta(days=cooldown_days)
            if next_allowed > now:
                continue
        if not user.last_active_at:
            continue
        db.add(
            NotificationORM(
                id=f"nt_{uuid4().hex[:10]}",
                user_id=user.id,
                title=title,
                body="Поверніться в ChallengeHub: у вас є челенджі, які чекають на прогрес.",
            )
        )
        user.last_comeback_notified_at = now
        created += 1
    if created:
        db.commit()
    return {"checked": len(users), "created": created}


@router.post("/assistant", response_model=AssistantResponse)
def assistant(
    payload: AssistantRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> AssistantResponse:
    user = db.get(MobileUserORM, current_user.id)
    if not user or not user.is_premium:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI assistant is available for Premium users only")
    answer, suggested_challenge_id = _call_gemini_assistant(payload.message, user, db)
    return AssistantResponse(answer=answer, suggested_challenge_id=suggested_challenge_id)


@router.post("/premium/checkout", response_model=PremiumCheckoutResponse)
def create_premium_checkout(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
) -> PremiumCheckoutResponse:
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured")
    success_url = f"{settings.stripe_success_url}{'&' if '?' in settings.stripe_success_url else '?'}session_id={{CHECKOUT_SESSION_ID}}"
    payload = urlencode(
        {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": settings.stripe_cancel_url,
            "line_items[0][price]": settings.stripe_price_id,
            "line_items[0][quantity]": "1",
            "client_reference_id": current_user.id,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.stripe_secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Stripe checkout failed") from exc
    return PremiumCheckoutResponse(checkout_url=data["url"])


def _premium_page(title: str, text: str, deep_link: str | None = None) -> str:
    auto_redirect = f"""
        <script>
          setTimeout(function () {{ window.location.href = "{deep_link}"; }}, 900);
        </script>
    """ if deep_link else ""
    action = f"""
          <a href="{deep_link}" style="display:inline-block;margin-top:22px;padding:14px 18px;border-radius:16px;background:linear-gradient(135deg,#AD46FF,#F6339A);color:white;text-decoration:none;font-weight:700">Повернутися в застосунок</a>
    """ if deep_link else ""
    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title}</title>
        {auto_redirect}
      </head>
      <body style="margin:0;background:#121212;color:white;font-family:Arial,sans-serif;display:grid;min-height:100vh;place-items:center">
        <main style="width:min(440px,calc(100vw - 32px));background:#1a1a1a;border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:32px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.45)">
          <div style="width:68px;height:68px;margin:0 auto 18px;border-radius:20px;background:linear-gradient(135deg,#AD46FF,#F6339A);display:grid;place-items:center;font-size:32px">★</div>
          <h1 style="margin:0 0 12px;font-size:26px">{title}</h1>
          <p style="margin:0;color:#bdbdbd;line-height:1.55">{text}</p>
          {action}
          <p style="margin:22px 0 0;color:#777;font-size:13px">Можна повернутися до застосунку ChallengeHub.</p>
        </main>
      </body>
    </html>
    """


@router.get("/premium/success", response_class=HTMLResponse)
def premium_success(
    session_id: str | None = None,
    user_id: str | None = None,
    db: Session = Depends(get_db),
) -> str:
    resolved_user_id = user_id
    if session_id:
        request = Request(
            f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
            headers={"Authorization": f"Bearer {settings.stripe_secret_key}"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=10) as response:
                session = json.loads(response.read().decode("utf-8"))
        except Exception:
            return _premium_page("Не вдалося перевірити оплату", "Stripe тимчасово не відповів. Спробуйте оновити сторінку або перевірити статус профілю пізніше.")
        if session.get("payment_status") not in {"paid", "no_payment_required"} and session.get("status") != "complete":
            return _premium_page("Оплата ще не завершена", "Premium буде активовано після успішного підтвердження платежу Stripe.")
        resolved_user_id = session.get("client_reference_id") or resolved_user_id

    if not resolved_user_id:
        return _premium_page("Не вдалося активувати Premium", "У посиланні відсутній ідентифікатор Stripe-сесії або користувача.")

    user = db.get(MobileUserORM, resolved_user_id)
    if not user:
        return _premium_page("Користувача не знайдено", "Оплата пройшла, але профіль ChallengeHub не знайдено. Зверніться до адміністратора.")

    if not user.is_premium:
        user.is_premium = True
        _refresh_user_badges(db, user)
        db.add(NotificationORM(id=f"nt_{uuid4().hex[:10]}", user_id=user.id, title="Premium активовано", body="Підписка ChallengeHub Premium успішно активована."))
        db.commit()
    deep_link = "challengehub://premium/success"
    if session_id:
        deep_link = f"{deep_link}?session_id={session_id}"
    return _premium_page("ChallengeHub Premium активовано", "Платіж підтверджено, Premium-функції вже доступні у вашому профілі.", deep_link)


@router.get("/premium/cancel", response_class=HTMLResponse)
def premium_cancel() -> str:
    return _premium_page("Оплату скасовано", "Premium не активовано. Ви можете повернутися до застосунку і спробувати ще раз.")
