from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.roles import WebRole
from app.infrastructure.db import TokenORM, WebUserORM, get_db
from app.schemas.auth import MeResponse

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
