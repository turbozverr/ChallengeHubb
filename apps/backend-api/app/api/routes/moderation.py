from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import ModerationVideoORM, ReportTicketORM, VideoLikeORM, get_db, to_dict
from app.schemas.auth import MeResponse
from app.schemas.moderation import (
    ModerationDecisionRequest,
    ModerationVideoResponse,
    ReportResponse,
    UpdateVideoRequest,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


def _likes_count_map(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(VideoLikeORM.video_id, func.count(VideoLikeORM.id))
        .group_by(VideoLikeORM.video_id)
    ).all()
    return {video_id: int(count) for video_id, count in rows}


def _video_response(video: ModerationVideoORM, likes_map: dict[str, int]) -> ModerationVideoResponse:
    data = to_dict(video)
    data["likes_count"] = likes_map.get(video.id, 0)
    return ModerationVideoResponse(**data)


@router.get("/videos/queue", response_model=list[ModerationVideoResponse])
def get_manual_moderation_queue(
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> list[ModerationVideoResponse]:
    require_roles({WebRole.ADMIN, WebRole.MODERATOR}, current_user)
    items = db.execute(
        select(ModerationVideoORM).where(ModerationVideoORM.status == "PENDING_MANUAL")
    ).scalars().all()
    likes_map = _likes_count_map(db)
    return [_video_response(item, likes_map) for item in items]


@router.post("/videos/{video_id}/decision", response_model=ModerationVideoResponse)
def decide_video(
    video_id: str,
    payload: ModerationDecisionRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> ModerationVideoResponse:
    require_roles({WebRole.ADMIN, WebRole.MODERATOR}, current_user)
    video = db.get(ModerationVideoORM, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if payload.decision not in {"APPROVE", "BLOCK"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported decision")
    video.status = "PUBLISHED" if payload.decision == "APPROVE" else "BLOCKED"
    video.decided_by = current_user.id
    video.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(video)
    likes_map = _likes_count_map(db)
    return _video_response(video, likes_map)


@router.get("/reports/queue", response_model=list[ReportResponse])
def get_reports_queue(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> list[ReportResponse]:
    require_roles({WebRole.ADMIN, WebRole.MODERATOR}, current_user)
    items = db.execute(select(ReportTicketORM).where(ReportTicketORM.status == "OPEN")).scalars().all()
    return [ReportResponse(**to_dict(item)) for item in items]


@router.post("/reports/{report_id}/decision", response_model=ReportResponse)
def decide_report(
    report_id: str,
    payload: ModerationDecisionRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    require_roles({WebRole.ADMIN, WebRole.MODERATOR}, current_user)
    report = db.get(ReportTicketORM, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if payload.decision not in {"CONFIRM", "REJECT"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported decision")
    report.status = "CONFIRMED" if payload.decision == "CONFIRM" else "REJECTED"
    report.decided_by = current_user.id
    report.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return ReportResponse(**to_dict(report))


@router.get("/videos", response_model=list[ModerationVideoResponse])
def list_all_videos(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> list[ModerationVideoResponse]:
    require_roles({WebRole.ADMIN}, current_user)
    rows = db.query(ModerationVideoORM).all()
    likes_map = _likes_count_map(db)
    return [_video_response(v, likes_map) for v in rows]


@router.patch("/videos/{video_id}", response_model=ModerationVideoResponse)
def update_video(
    video_id: str,
    payload: UpdateVideoRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> ModerationVideoResponse:
    require_roles({WebRole.ADMIN}, current_user)
    video = db.get(ModerationVideoORM, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if payload.url is not None:
        video.url = payload.url
    if payload.description is not None:
        video.description = payload.description
    if payload.status is not None:
        video.status = payload.status
    if payload.is_ad is not None:
        video.is_ad = payload.is_ad
    db.commit()
    db.refresh(video)
    likes_map = _likes_count_map(db)
    return _video_response(video, likes_map)


@router.delete("/videos/{video_id}")
def delete_video(
    video_id: str,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    require_roles({WebRole.ADMIN}, current_user)
    video = db.get(ModerationVideoORM, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    db.query(ReportTicketORM).filter(ReportTicketORM.video_id == video_id).delete()
    db.query(VideoLikeORM).filter(VideoLikeORM.video_id == video_id).delete()
    db.delete(video)
    db.commit()
    return {"ok": True}
