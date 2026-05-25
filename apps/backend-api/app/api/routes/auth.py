from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user
from app.domain.roles import WebRole
from app.infrastructure.db import TokenORM, WebUserORM, get_db
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(WebUserORM).where(WebUserORM.email == payload.email)).scalar_one_or_none()
    if not user or user.password != payload.password:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    from uuid import uuid4

    token = f"token_{uuid4().hex}"
    db.add(TokenORM(token=token, user_id=user.id))
    db.commit()
    return TokenResponse(
        access_token=token,
        user=MeResponse(id=user.id, full_name=user.full_name, email=user.email, role=WebRole(user.role)),
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: MeResponse = Depends(get_current_web_user)) -> MeResponse:
    return current_user
