from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.models import ModerationVideo, ReportTicket, SponsoredChallenge, WebUser
from app.domain.roles import WebRole


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class MemoryStore:
    def __init__(self) -> None:
        self.web_users: dict[str, WebUser] = {}
        self.sponsored_challenges: dict[str, SponsoredChallenge] = {}
        self.videos: dict[str, ModerationVideo] = {}
        self.reports: dict[str, ReportTicket] = {}
        self.tokens: dict[str, str] = {}
        self._seed()

    def _seed(self) -> None:
        admin = WebUser(
            id="w_admin_1",
            full_name="Admin ChallengeHub",
            email="admin@challengehub.dev",
            role=WebRole.ADMIN,
            password="12345",
        )
        moderator = WebUser(
            id="w_mod_1",
            full_name="Moderator ChallengeHub",
            email="moderator@challengehub.dev",
            role=WebRole.MODERATOR,
            password="12345",
        )
        business = WebUser(
            id="w_biz_1",
            full_name="Brand Manager EVA",
            email="business@challengehub.dev",
            role=WebRole.BUSINESS_CLIENT,
            password="12345",
            company_name="EVA",
        )

        self.web_users = {u.id: u for u in [admin, moderator, business]}

        ch = SponsoredChallenge(
            id="sp_1",
            title="EVA Spring Challenge",
            description="Зніми відео з покупкою набору гігієни EVA",
            reward_text="Промокод на парфум",
            client_id=business.id,
            client_company_name=business.company_name or "Unknown",
            status="PUBLISHED",
            created_by_admin_id=admin.id,
            published_at=datetime.now(timezone.utc),
        )
        self.sponsored_challenges[ch.id] = ch

        v1 = ModerationVideo(
            id="vid_1",
            challenge_id=ch.id,
            author_user_id="mobile_user_1",
            url="https://cdn.challengehub.local/video/1",
            ai_status="REJECTED",
            status="PENDING_MANUAL",
            reports_count=1,
        )
        v2 = ModerationVideo(
            id="vid_2",
            challenge_id=ch.id,
            author_user_id="mobile_user_2",
            url="https://cdn.challengehub.local/video/2",
            ai_status="APPROVED",
            status="PUBLISHED",
            reports_count=4,
        )
        self.videos[v1.id] = v1
        self.videos[v2.id] = v2

        r1 = ReportTicket(
            id="rep_1",
            video_id=v2.id,
            reason="Підозра на недоречний контент",
            status="OPEN",
        )
        self.reports[r1.id] = r1

    def create_token_for_user(self, user_id: str) -> str:
        token = f"token_{uuid4().hex}"
        self.tokens[token] = user_id
        return token

    def get_user_by_token(self, token: str) -> WebUser | None:
        user_id = self.tokens.get(token)
        if not user_id:
            return None
        return self.web_users.get(user_id)

    def find_user_by_email(self, email: str) -> WebUser | None:
        for user in self.web_users.values():
            if user.email.lower() == email.lower():
                return user
        return None

    def create_web_user(
        self, full_name: str, email: str, password: str, role: WebRole, company_name: str | None = None
    ) -> WebUser:
        user = WebUser(
            id=_id("w"),
            full_name=full_name,
            email=email,
            password=password,
            role=role,
            company_name=company_name,
        )
        self.web_users[user.id] = user
        return user

    def create_sponsored_challenge(
        self,
        title: str,
        description: str,
        reward_text: str,
        client_id: str,
        client_company_name: str,
        admin_id: str,
    ) -> SponsoredChallenge:
        challenge = SponsoredChallenge(
            id=_id("sp"),
            title=title,
            description=description,
            reward_text=reward_text,
            client_id=client_id,
            client_company_name=client_company_name,
            status="DRAFT",
            created_by_admin_id=admin_id,
        )
        self.sponsored_challenges[challenge.id] = challenge
        return challenge

    def publish_sponsored_challenge(self, challenge_id: str) -> SponsoredChallenge | None:
        challenge = self.sponsored_challenges.get(challenge_id)
        if not challenge:
            return None
        challenge.status = "PUBLISHED"
        challenge.published_at = datetime.now(timezone.utc)
        return challenge


store = MemoryStore()


def to_dict(obj: object) -> dict:
    raw = asdict(obj)
    for key, value in raw.items():
        if isinstance(value, datetime):
            raw[key] = value.isoformat()
    return raw
