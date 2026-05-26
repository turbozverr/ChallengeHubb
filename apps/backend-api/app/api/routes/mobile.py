from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_mobile_user
from app.core.config import settings
from app.infrastructure.db import (
    ChallengeParticipationORM,
    MobileTokenORM,
    MobileUserORM,
    ModerationVideoORM,
    NotificationORM,
    ReportTicketORM,
    SponsoredChallengeORM,
    SystemSettingsORM,
    UserBadgeORM,
    UserChallengeORM,
    VideoCommentORM,
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
    ReportVideoRequest,
    UpdateMobileProfileRequest,
)

router = APIRouter(prefix="/mobile", tags=["mobile"])


def _mobile_user_response(user: MobileUserORM) -> MobileUserResponse:
    return MobileUserResponse(**to_dict(user))


def _video_response(video: ModerationVideoORM, db: Session, current_user_id: str | None = None) -> MobileVideoResponse:
    data = to_dict(video)
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
    return MobileVideoResponse(**data)


def _challenge_response(row: SponsoredChallengeORM | UserChallengeORM, challenge_type: str, creator_name: str | None = None) -> MobileChallengeResponse:
    data = to_dict(row)
    data["challenge_type"] = challenge_type
    data["creator_name"] = creator_name
    return MobileChallengeResponse(**data)


def _issue_mobile_token(user: MobileUserORM, db: Session) -> MobileTokenResponse:
    user.last_active_at = now_utc()
    token = f"mobile_{uuid4().hex}"
    db.add(MobileTokenORM(token=token, user_id=user.id))
    db.commit()
    db.refresh(user)
    return MobileTokenResponse(access_token=token, user=_mobile_user_response(user))


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
        xp=0,
        is_premium=False,
        status="ACTIVE",
        last_active_at=now_utc(),
    )
    token = f"mobile_{uuid4().hex}"
    db.add(user)
    db.add(MobileTokenORM(token=token, user_id=user.id))
    db.commit()
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
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token}"
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
        username = f"g_{email.split('@')[0]}".replace(".", "_")[:64]
        user = MobileUserORM(
            id=f"mu_{uuid4().hex[:10]}",
            username=username,
            full_name=name,
            email=email,
            password="GOOGLE_OAUTH",
            avatar_url=data.get("picture"),
            xp=0,
            is_premium=False,
            status="ACTIVE",
            last_active_at=now_utc(),
        )
        db.add(user)
        db.flush()
    return _issue_mobile_token(user, db)


@router.get("/auth/me", response_model=MobileUserResponse)
def mobile_me(current_user: MobileUserResponse = Depends(get_current_mobile_user)) -> MobileUserResponse:
    return current_user


@router.get("/feed", response_model=list[MobileVideoResponse])
def get_feed(db: Session = Depends(get_db)) -> list[MobileVideoResponse]:
    videos = (
        db.execute(select(ModerationVideoORM).where(ModerationVideoORM.status == "PUBLISHED").order_by(ModerationVideoORM.created_at.desc()))
        .scalars()
        .all()
    )
    return [_video_response(video, db) for video in videos]


@router.get("/challenges", response_model=list[MobileChallengeResponse])
def list_mobile_challenges(db: Session = Depends(get_db)) -> list[MobileChallengeResponse]:
    sponsored = db.execute(select(SponsoredChallengeORM).where(SponsoredChallengeORM.status == "PUBLISHED")).scalars().all()
    regular = db.execute(select(UserChallengeORM).where(UserChallengeORM.status == "PUBLISHED")).scalars().all()
    creators = {u.id: u.full_name for u in db.execute(select(MobileUserORM)).scalars().all()}
    result = [_challenge_response(item, "SPONSORED") for item in sponsored]
    result.extend(_challenge_response(item, "USER", creators.get(item.created_by_user_id)) for item in regular)
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
    db.commit()
    db.refresh(challenge)
    return _challenge_response(challenge, "USER", current_user.full_name)


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
    video = ModerationVideoORM(
        id=f"vid_{uuid4().hex[:10]}",
        challenge_id=challenge_id,
        challenge_type=challenge_type,
        author_user_id=current_user.id,
        url=str(target).replace("\\", "/"),
        description=description,
        ai_status="APPROVED",
        status="PUBLISHED",
        reports_count=0,
        is_ad=False,
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
    if participation:
        participation.status = "COMPLETED"
        participation.completed_at = now_utc()
    user = db.get(MobileUserORM, current_user.id)
    if user:
        user.xp += min(challenge.xp_reward, 2000 if challenge_type == "SPONSORED" else 500)
    db.add(video)
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
        video.likes_count += 1
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
        video.likes_count = max(0, video.likes_count - 1)
        db.commit()
        db.refresh(video)
    return _video_response(video, db, current_user.id)


@router.get("/videos/{video_id}/comments", response_model=list[CommentResponse])
def list_comments(video_id: str, db: Session = Depends(get_db)) -> list[CommentResponse]:
    comments = db.execute(select(VideoCommentORM).where(VideoCommentORM.video_id == video_id).order_by(VideoCommentORM.created_at.asc())).scalars().all()
    users = {u.id: u.username for u in db.execute(select(MobileUserORM)).scalars().all()}
    return [CommentResponse(**to_dict(comment), username=users.get(comment.user_id, "unknown")) for comment in comments]


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
    return CommentResponse(**to_dict(comment), username=current_user.username)


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
    video.reports_count += 1
    settings = db.get(SystemSettingsORM, "settings_main")
    if settings and video.reports_count >= settings.report_limit:
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
    for field in ["username", "full_name", "bio", "avatar_url"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)
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
    rows = db.execute(select(UserBadgeORM).where(UserBadgeORM.user_id == current_user.id)).scalars().all()
    return [BadgeResponse(**to_dict(row)) for row in rows]


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
def get_leaderboard(db: Session = Depends(get_db)) -> list[LeaderboardEntryResponse]:
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


@router.post("/assistant", response_model=AssistantResponse)
def assistant(
    payload: AssistantRequest,
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
    db: Session = Depends(get_db),
) -> AssistantResponse:
    user = db.get(MobileUserORM, current_user.id)
    challenge = db.execute(select(SponsoredChallengeORM).where(SponsoredChallengeORM.status == "PUBLISHED")).scalar_one_or_none()
    xp = user.xp if user else 0
    answer = (
        f"Ти маєш {xp} XP. Спробуй короткий челендж сьогодні: запиши відео до 30 секунд, "
        "додай опис і не забувай про стабільний темп. Якщо бракує ідей, обери челендж із найбільшою XP-нагородою."
    )
    if payload.message:
        answer = f"Я почув запит: \"{payload.message}\". {answer}"
    return AssistantResponse(answer=answer, suggested_challenge_id=challenge.id if challenge else None)


@router.post("/premium/checkout", response_model=PremiumCheckoutResponse)
def create_premium_checkout(
    current_user: MobileUserResponse = Depends(get_current_mobile_user),
) -> PremiumCheckoutResponse:
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured")
    payload = urlencode(
        {
            "mode": "subscription",
            "success_url": settings.stripe_success_url,
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
