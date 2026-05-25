from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import ModerationVideoORM, ReportTicketORM, SponsoredChallengeORM, WebUserORM, get_db
from app.schemas.auth import MeResponse

router = APIRouter(prefix="/admin", tags=["admin"])


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
