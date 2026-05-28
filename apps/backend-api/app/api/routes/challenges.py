from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import (
    AdVideoORM,
    PromoCodeORM,
    SponsoredChallengeORM,
    WebUserORM,
    get_db,
    now_utc,
    to_dict,
)
from app.schemas.auth import MeResponse
from app.schemas.challenges import (
    AdVideoResponse,
    CreateSponsoredChallengeRequest,
    PromoCodeResponse,
    SponsoredChallengeResponse,
    UpdateSponsoredChallengeRequest,
)

router = APIRouter(prefix="/sponsored-challenges", tags=["sponsored-challenges"])


@router.get("/promo/unsent", response_model=list[PromoCodeResponse])
def unsent_promo_codes(current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> list[PromoCodeResponse]:
    require_roles({WebRole.ADMIN, WebRole.BUSINESS_CLIENT}, current_user)
    query = db.query(PromoCodeORM).join(SponsoredChallengeORM, SponsoredChallengeORM.id == PromoCodeORM.challenge_id)
    if current_user.role == WebRole.BUSINESS_CLIENT:
        query = query.filter(SponsoredChallengeORM.client_id == current_user.id)
    rows = query.filter(PromoCodeORM.is_sent == False).all()  # noqa: E712
    return [PromoCodeResponse(**to_dict(row)) for row in rows]


@router.get("/{challenge_id}/promo-codes", response_model=list[PromoCodeResponse])
def get_challenge_promo_codes(
    challenge_id: str,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> list[PromoCodeResponse]:
    require_roles({WebRole.ADMIN, WebRole.BUSINESS_CLIENT}, current_user)
    challenge = db.get(SponsoredChallengeORM, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    if current_user.role == WebRole.BUSINESS_CLIENT and challenge.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    rows = db.query(PromoCodeORM).filter(PromoCodeORM.challenge_id == challenge_id).all()
    return [PromoCodeResponse(**to_dict(row)) for row in rows]


@router.get("/ad-videos", response_model=list[AdVideoResponse])
def list_ad_videos(current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> list[AdVideoResponse]:
    require_roles({WebRole.ADMIN, WebRole.BUSINESS_CLIENT, WebRole.MODERATOR}, current_user)
    rows = db.query(AdVideoORM).all()
    return [AdVideoResponse(**to_dict(row)) for row in rows]


@router.post("/ad-videos", response_model=AdVideoResponse)
async def upload_ad_video(
    description: str = Form(...),
    file: UploadFile = File(...),
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> AdVideoResponse:
    require_roles({WebRole.ADMIN}, current_user)
    uploads_dir = Path("uploads/ad-videos")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "video.bin").suffix or ".bin"
    file_name = f"ad_{uuid4().hex}{suffix}"
    target = uploads_dir / file_name
    content = await file.read()
    target.write_bytes(content)
    row = AdVideoORM(
        id=f"ad_{uuid4().hex[:10]}",
        description=description,
        url=None,
        file_path=str(target).replace("\\", "/"),
        created_by_admin_id=current_user.id,
        status="PUBLISHED",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AdVideoResponse(**to_dict(row))


@router.patch("/ad-videos/{ad_video_id}", response_model=AdVideoResponse)
def update_ad_video(
    ad_video_id: str,
    description: str | None = Form(default=None),
    status_value: str | None = Form(default=None, alias="status"),
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> AdVideoResponse:
    require_roles({WebRole.ADMIN}, current_user)
    row = db.get(AdVideoORM, ad_video_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad video not found")
    if description is not None:
        row.description = description
    if status_value is not None:
        row.status = status_value
    db.commit()
    db.refresh(row)
    return AdVideoResponse(**to_dict(row))


@router.delete("/ad-videos/{ad_video_id}")
def delete_ad_video(
    ad_video_id: str,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    require_roles({WebRole.ADMIN}, current_user)
    row = db.get(AdVideoORM, ad_video_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad video not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("", response_model=list[SponsoredChallengeResponse])
def list_sponsored_challenges(current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> list[SponsoredChallengeResponse]:
    require_roles({WebRole.ADMIN, WebRole.MODERATOR}, current_user)
    rows = db.execute(select(SponsoredChallengeORM)).scalars().all()
    return [SponsoredChallengeResponse(**to_dict(item)) for item in rows]


@router.post("", response_model=SponsoredChallengeResponse)
def create_sponsored_challenge(payload: CreateSponsoredChallengeRequest, current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> SponsoredChallengeResponse:
    require_roles({WebRole.ADMIN}, current_user)
    client = db.get(WebUserORM, payload.client_id)
    if not client or client.role != WebRole.BUSINESS_CLIENT.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid business client")
    challenge = SponsoredChallengeORM(
        id=f"sp_{uuid4().hex[:10]}",
        title=payload.title,
        description=payload.description,
        reward_text=payload.reward_text,
        difficulty=payload.difficulty,
        duration_days=payload.duration_days,
        xp_reward=max(1, min(payload.xp_reward, 2000)),
        promo_mode=payload.promo_mode,
        promo_single_code=payload.promo_single_code,
        client_id=client.id,
        client_company_name=client.company_name or "Unknown",
        status="DRAFT",
        created_by_admin_id=current_user.id,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    if payload.promo_mode == "LIST" and payload.promo_codes:
        for code in payload.promo_codes:
            db.add(PromoCodeORM(id=f"pc_{uuid4().hex[:10]}", challenge_id=challenge.id, code=code, is_sent=False))
        db.commit()
    return SponsoredChallengeResponse(**to_dict(challenge))


@router.post("/{challenge_id}/publish", response_model=SponsoredChallengeResponse)
def publish_sponsored_challenge(challenge_id: str, current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> SponsoredChallengeResponse:
    require_roles({WebRole.ADMIN}, current_user)
    challenge = db.get(SponsoredChallengeORM, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    challenge.status = "PUBLISHED"
    challenge.published_at = now_utc()
    db.commit()
    db.refresh(challenge)
    return SponsoredChallengeResponse(**to_dict(challenge))


@router.patch("/{challenge_id}", response_model=SponsoredChallengeResponse)
def update_sponsored_challenge(challenge_id: str, payload: UpdateSponsoredChallengeRequest, current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> SponsoredChallengeResponse:
    require_roles({WebRole.ADMIN}, current_user)
    challenge = db.get(SponsoredChallengeORM, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    for field in ["title", "description", "reward_text", "difficulty", "duration_days", "status"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(challenge, field, value)
    if payload.xp_reward is not None:
        challenge.xp_reward = max(1, min(payload.xp_reward, 2000))
    if payload.promo_mode is not None:
        challenge.promo_mode = payload.promo_mode
    if payload.promo_single_code is not None:
        challenge.promo_single_code = payload.promo_single_code
    if payload.promo_codes is not None:
        db.query(PromoCodeORM).filter(PromoCodeORM.challenge_id == challenge_id).delete()
        if challenge.promo_mode == "LIST":
            for code in payload.promo_codes:
                code_norm = code.strip()
                if not code_norm:
                    continue
                db.add(PromoCodeORM(id=f"pc_{uuid4().hex[:10]}", challenge_id=challenge.id, code=code_norm, is_sent=False))
    db.commit()
    db.refresh(challenge)
    return SponsoredChallengeResponse(**to_dict(challenge))


@router.delete("/{challenge_id}")
def delete_sponsored_challenge(challenge_id: str, current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    require_roles({WebRole.ADMIN}, current_user)
    challenge = db.get(SponsoredChallengeORM, challenge_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    db.query(PromoCodeORM).filter(PromoCodeORM.challenge_id == challenge_id).delete()
    db.delete(challenge)
    db.commit()
    return {"ok": True}
