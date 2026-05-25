from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import SystemSettingsORM, get_db, to_dict
from app.schemas.auth import MeResponse
from app.schemas.settings import SystemSettingsResponse, UpdateSystemSettingsRequest

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SystemSettingsResponse)
def get_settings(current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)) -> SystemSettingsResponse:
    require_roles({WebRole.ADMIN}, current_user)
    row = db.get(SystemSettingsORM, "settings_main")
    if not row:
        row = SystemSettingsORM(id="settings_main", ai_confidence_threshold=0.85, report_limit=3)
        db.add(row)
        db.commit()
        db.refresh(row)
    return SystemSettingsResponse(**to_dict(row))


@router.patch("", response_model=SystemSettingsResponse)
def update_settings(
    payload: UpdateSystemSettingsRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> SystemSettingsResponse:
    require_roles({WebRole.ADMIN}, current_user)
    row = db.get(SystemSettingsORM, "settings_main")
    if not row:
        row = SystemSettingsORM(id="settings_main", ai_confidence_threshold=0.85, report_limit=3)
        db.add(row)
        db.flush()
    if payload.ai_confidence_threshold is not None:
        row.ai_confidence_threshold = payload.ai_confidence_threshold
    if payload.report_limit is not None:
        row.report_limit = payload.report_limit
    db.commit()
    db.refresh(row)
    return SystemSettingsResponse(**to_dict(row))
