from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.roles import WebRole
from app.infrastructure.db import MobileTokenORM, MobileUserORM, TokenORM, WebUserORM, get_db
from app.schemas.auth import MeResponse
from app.schemas.mobile import MobileUserResponse

bearer = HTTPBearer(auto_error=False)


def _to_me_response(user: WebUserORM) -> MeResponse:
    return MeResponse(id=user.id, full_name=user.full_name, email=user.email, role=WebRole(user.role))


def get_current_web_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> MeResponse:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token_row = db.get(TokenORM, credentials.credentials)
    user = db.get(WebUserORM, token_row.user_id) if token_row else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return _to_me_response(user)


def require_roles(allowed: set[WebRole], user: MeResponse) -> None:
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )


def _to_mobile_response(user: MobileUserORM) -> MobileUserResponse:
    premium_active = bool(user.premium_until and user.premium_until > datetime.now(timezone.utc))
    return MobileUserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        auth_provider=user.auth_provider,
        avatar_url=user.avatar_url,
        profile_background=user.profile_background,
        xp=user.xp,
        is_premium=premium_active,
        premium_until=user.premium_until.isoformat() if user.premium_until else None,
        status=user.status,
        created_at=user.created_at.isoformat(),
    )


def get_current_mobile_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> MobileUserResponse:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token_row = db.get(MobileTokenORM, credentials.credentials)
    user = db.get(MobileUserORM, token_row.user_id) if token_row else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return _to_mobile_response(user)
