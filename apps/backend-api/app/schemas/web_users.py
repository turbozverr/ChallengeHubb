from pydantic import BaseModel

from app.domain.roles import WebRole


class CreateWebUserRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: WebRole
    company_name: str | None = None


class WebUserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: WebRole
    company_name: str | None = None
    is_active: bool
    created_at: str


class UpdateWebUserRequest(BaseModel):
    full_name: str | None = None
    role: WebRole | None = None
    company_name: str | None = None
    is_active: bool | None = None
