from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_web_user, require_roles
from app.domain.roles import WebRole
from app.infrastructure.db import WebUserORM, get_db, to_dict
from app.schemas.auth import MeResponse
from app.schemas.web_users import CreateWebUserRequest, UpdateWebUserRequest, WebUserResponse

router = APIRouter(prefix="/web-users", tags=["web-users"])


@router.get("", response_model=list[WebUserResponse])
def list_web_users(
    current_user: MeResponse = Depends(get_current_web_user), db: Session = Depends(get_db)
) -> list[WebUserResponse]:
    require_roles({WebRole.ADMIN}, current_user)
    users = db.execute(select(WebUserORM)).scalars().all()
    return [WebUserResponse(**to_dict(user)) for user in users]


@router.post("", response_model=WebUserResponse)
def create_web_user(
    payload: CreateWebUserRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> WebUserResponse:
    require_roles({WebRole.ADMIN}, current_user)
    exists = db.execute(select(WebUserORM).where(WebUserORM.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    from uuid import uuid4

    user = WebUserORM(
        id=f"w_{uuid4().hex[:10]}",
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role.value,
        company_name=payload.company_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return WebUserResponse(**to_dict(user))


@router.patch("/{user_id}", response_model=WebUserResponse)
def update_web_user(
    user_id: str,
    payload: UpdateWebUserRequest,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> WebUserResponse:
    require_roles({WebRole.ADMIN}, current_user)
    user = db.get(WebUserORM, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role.value
    if payload.company_name is not None:
        user.company_name = payload.company_name
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return WebUserResponse(**to_dict(user))


@router.delete("/{user_id}")
def delete_web_user(
    user_id: str,
    current_user: MeResponse = Depends(get_current_web_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    require_roles({WebRole.ADMIN}, current_user)
    user = db.get(WebUserORM, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return {"ok": True}
