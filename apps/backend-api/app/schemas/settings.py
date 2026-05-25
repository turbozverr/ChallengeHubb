from pydantic import BaseModel


class SystemSettingsResponse(BaseModel):
    id: str
    ai_confidence_threshold: float
    report_limit: int


class UpdateSystemSettingsRequest(BaseModel):
    ai_confidence_threshold: float | None = None
    report_limit: int | None = None
