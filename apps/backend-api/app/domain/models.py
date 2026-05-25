from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.roles import WebRole


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WebUser:
    id: str
    full_name: str
    email: str
    role: WebRole
    password: str
    company_name: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=now_utc)


@dataclass
class SponsoredChallenge:
    id: str
    title: str
    description: str
    reward_text: str
    client_id: str
    client_company_name: str
    status: str
    created_by_admin_id: str
    created_at: datetime = field(default_factory=now_utc)
    published_at: datetime | None = None


@dataclass
class ModerationVideo:
    id: str
    challenge_id: str
    author_user_id: str
    url: str
    ai_status: str
    status: str
    reports_count: int = 0
    created_at: datetime = field(default_factory=now_utc)
    decided_by: str | None = None
    decided_at: datetime | None = None


@dataclass
class ReportTicket:
    id: str
    video_id: str
    reason: str
    status: str
    created_at: datetime = field(default_factory=now_utc)
    decided_by: str | None = None
    decided_at: datetime | None = None
