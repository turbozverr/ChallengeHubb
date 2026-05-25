from pydantic import BaseModel

from app.domain.roles import WebRole


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "MeResponse"


class MeResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: WebRole


TokenResponse.model_rebuild()
