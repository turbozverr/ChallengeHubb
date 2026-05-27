from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import (
    ChallengeParticipationORM,
    MobileTokenORM,
    MobileUserORM,
    ModerationVideoORM,
    NotificationORM,
    ReportTicketORM,
    SponsoredChallengeORM,
    UserBadgeORM,
    UserChallengeORM,
    VideoCommentLikeORM,
    VideoCommentORM,
    VideoLikeORM,
    WebUserORM,
    get_db,
    to_dict,
)
from app.schemas.auth import MeResponse
from app.schemas.mobile import MobileUserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class UpdateMobileUserRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)


@router.get("/panel")
def admin_panel(current_user: MeResponse = Depends(get_current_web_user)) -> dict[str, str]:
    require_roles({WebRole.ADMIN}, current_user)
    return {"message": "Admin panel API доступний"}


@router.get("/overview")
def admin_overview(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> dict[str, int]:
    require_roles({WebRole.ADMIN}, current_user)
    return {
        "web_users_total": db.scalar(select(func.count()).select_from(WebUserORM)) or 0,
        "sponsored_challenges_total": db.scalar(select(func.count()).select_from(SponsoredChallengeORM)) or 0,
        "videos_pending_manual": db.scalar(
            select(func.count()).select_from(ModerationVideoORM).where(ModerationVideoORM.status == "PENDING_MANUAL")
        )
        or 0,
        "open_reports": db.scalar(
            select(func.count()).select_from(ReportTicketORM).where(ReportTicketORM.status == "OPEN")
        )
        or 0,
    }


@router.get("/mobile-users", response_model=list[MobileUserResponse])
def list_mobile_users(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> list[MobileUserResponse]:
    require_roles({WebRole.ADMIN}, current_user)
    users = db.execute(select(MobileUserORM)).scalars().all()
    return [MobileUserResponse(**to_dict(user)) for user in users]


@router.patch("/mobile-users/{user_id}", response_model=MobileUserResponse)
def update_mobile_user(
    user_id: str,
    payload: UpdateMobileUserRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> MobileUserResponse:
    require_roles({WebRole.ADMIN}, current_user)
    user = db.get(MobileUserORM, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mobile user not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    db.commit()
    db.refresh(user)
    return MobileUserResponse(**to_dict(user))


@router.delete("/mobile-users/{user_id}")
def delete_mobile_user(
    user_id: str,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    require_roles({WebRole.ADMIN}, current_user)
    user = db.get(MobileUserORM, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mobile user not found")

    authored_video_ids = [
        row[0]
        for row in db.execute(
            select(ModerationVideoORM.id).where(ModerationVideoORM.author_user_id == user_id)
        ).all()
    ]
    authored_comment_ids = [
        row[0]
        for row in db.execute(select(VideoCommentORM.id).where(VideoCommentORM.user_id == user_id)).all()
    ]
    video_comment_ids: list[str] = []
    if authored_video_ids:
        video_comment_ids = [
            row[0]
            for row in db.execute(select(VideoCommentORM.id).where(VideoCommentORM.video_id.in_(authored_video_ids))).all()
        ]

    comment_ids = list(set(authored_comment_ids + video_comment_ids))
    if comment_ids:
        db.query(VideoCommentLikeORM).filter(VideoCommentLikeORM.comment_id.in_(comment_ids)).delete(
            synchronize_session=False
        )
    db.query(VideoCommentLikeORM).filter(VideoCommentLikeORM.user_id == user_id).delete(synchronize_session=False)
    db.query(VideoCommentORM).filter(VideoCommentORM.user_id == user_id).delete(synchronize_session=False)
    if authored_video_ids:
        db.query(VideoCommentORM).filter(VideoCommentORM.video_id.in_(authored_video_ids)).delete(
            synchronize_session=False
        )
        db.query(ReportTicketORM).filter(ReportTicketORM.video_id.in_(authored_video_ids)).delete(
            synchronize_session=False
        )
        db.query(VideoLikeORM).filter(VideoLikeORM.video_id.in_(authored_video_ids)).delete(
            synchronize_session=False
        )
        db.query(ModerationVideoORM).filter(ModerationVideoORM.id.in_(authored_video_ids)).delete(
            synchronize_session=False
        )

    db.query(VideoLikeORM).filter(VideoLikeORM.user_id == user_id).delete(synchronize_session=False)
    db.query(ChallengeParticipationORM).filter(ChallengeParticipationORM.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(UserChallengeORM).filter(UserChallengeORM.created_by_user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(UserBadgeORM).filter(UserBadgeORM.user_id == user_id).delete(synchronize_session=False)
    db.query(NotificationORM).filter(NotificationORM.user_id == user_id).delete(synchronize_session=False)
    db.query(MobileTokenORM).filter(MobileTokenORM.user_id == user_id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return {"ok": True}
