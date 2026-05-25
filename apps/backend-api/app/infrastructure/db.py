from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import settings
from app.domain.roles import WebRole


class Base(DeclarativeBase):
    pass


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class WebUserORM(Base):
    __tablename__ = "web_users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class TokenORM(Base):
    __tablename__ = "auth_tokens"
    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("web_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class SponsoredChallengeORM(Base):
    __tablename__ = "sponsored_challenges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reward_text: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default="normal")
    duration_days: Mapped[int] = mapped_column(Integer, default=7)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    promo_mode: Mapped[str] = mapped_column(String(32), default="SINGLE")
    promo_single_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("web_users.id"), nullable=False)
    client_company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by_admin_id: Mapped[str] = mapped_column(ForeignKey("web_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PromoCodeORM(Base):
    __tablename__ = "promo_codes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    challenge_id: Mapped[str] = mapped_column(ForeignKey("sponsored_challenges.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(255), nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)


class ModerationVideoORM(Base):
    __tablename__ = "moderation_videos"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    challenge_id: Mapped[str] = mapped_column(ForeignKey("sponsored_challenges.id"), nullable=False)
    author_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_status: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reports_count: Mapped[int] = mapped_column(Integer, default=0)
    is_ad: Mapped[bool] = mapped_column(Boolean, default=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    shares_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportTicketORM(Base):
    __tablename__ = "report_tickets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("moderation_videos.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VideoLikeORM(Base):
    __tablename__ = "video_likes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    video_id: Mapped[str] = mapped_column(ForeignKey("moderation_videos.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AdVideoORM(Base):
    __tablename__ = "ad_videos"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    challenge_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class SystemSettingsORM(Base):
    __tablename__ = "system_settings"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ai_confidence_threshold: Mapped[float] = mapped_column(Float, default=0.85)
    report_limit: Mapped[int] = mapped_column(Integer, default=3)


engine = create_engine(settings.mysql_dsn, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def to_dict(obj: object) -> dict:
    data: dict[str, object] = {}
    for column in obj.__table__.columns:  # type: ignore[attr-defined]
        value = getattr(obj, column.name)
        data[column.name] = value.isoformat() if isinstance(value, datetime) else value
    return data


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        migrations = [
            "ALTER TABLE sponsored_challenges ADD COLUMN difficulty VARCHAR(16) DEFAULT 'normal'",
            "ALTER TABLE sponsored_challenges ADD COLUMN duration_days INT DEFAULT 7",
            "ALTER TABLE sponsored_challenges ADD COLUMN xp_reward INT DEFAULT 100",
            "ALTER TABLE sponsored_challenges ADD COLUMN promo_mode VARCHAR(32) DEFAULT 'SINGLE'",
            "ALTER TABLE sponsored_challenges ADD COLUMN promo_single_code VARCHAR(255) NULL",
            "ALTER TABLE moderation_videos ADD COLUMN is_ad BOOLEAN DEFAULT FALSE",
            "ALTER TABLE moderation_videos ADD COLUMN description TEXT NULL",
            "ALTER TABLE moderation_videos ADD COLUMN views_count INT DEFAULT 0",
            "ALTER TABLE moderation_videos ADD COLUMN likes_count INT DEFAULT 0",
            "ALTER TABLE moderation_videos ADD COLUMN shares_count INT DEFAULT 0",
            "CREATE TABLE IF NOT EXISTS video_likes (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, video_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE UNIQUE INDEX ux_video_likes_user_video ON video_likes (user_id, video_id)",
            "ALTER TABLE video_likes DROP FOREIGN KEY video_likes_ibfk_1",
            "ALTER TABLE video_likes DROP FOREIGN KEY fk_video_likes_video",
            "ALTER TABLE video_likes ADD CONSTRAINT fk_video_likes_video FOREIGN KEY (video_id) REFERENCES moderation_videos(id) ON DELETE CASCADE",
            "CREATE TABLE IF NOT EXISTS promo_codes (id VARCHAR(64) PRIMARY KEY, challenge_id VARCHAR(64) NOT NULL, code VARCHAR(255) NOT NULL, is_sent BOOLEAN DEFAULT FALSE)",
            "CREATE TABLE IF NOT EXISTS ad_videos (id VARCHAR(64) PRIMARY KEY, challenge_id VARCHAR(64) NULL, title VARCHAR(255) NOT NULL, video_url TEXT NULL, file_path TEXT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS system_settings (id VARCHAR(64) PRIMARY KEY, ai_confidence_threshold FLOAT DEFAULT 0.85, report_limit INT DEFAULT 3)",
            "ALTER TABLE ad_videos ADD COLUMN file_path TEXT NULL",
            "ALTER TABLE ad_videos MODIFY COLUMN challenge_id VARCHAR(64) NULL",
            "ALTER TABLE ad_videos MODIFY COLUMN video_url TEXT NULL",
        ]
        for statement in migrations:
            try:
                conn.execute(text(statement))
            except Exception:
                pass
    with SessionLocal() as db:
        if db.query(WebUserORM).count() > 0:
            return
        admin = WebUserORM(id="w_admin_1", full_name="Admin ChallengeHub", email="admin@challengehub.local", role=WebRole.ADMIN.value, password="admin123")
        moderator = WebUserORM(id="w_mod_1", full_name="Moderator ChallengeHub", email="moderator@challengehub.local", role=WebRole.MODERATOR.value, password="moderator123")
        business = WebUserORM(id="w_biz_1", full_name="Brand Manager EVA", email="business@challengehub.local", role=WebRole.BUSINESS_CLIENT.value, password="business123", company_name="EVA")
        db.add_all([admin, moderator, business])
        db.flush()
        challenge = SponsoredChallengeORM(
            id="sp_1",
            title="EVA Spring Challenge",
            description="Зніми відео з покупкою набору гігієни EVA",
            reward_text="Промокод на парфум",
            difficulty="normal",
            duration_days=7,
            xp_reward=200,
            promo_mode="SINGLE",
            promo_single_code="EVA-PARFUM-2026",
            client_id=business.id,
            client_company_name="EVA",
            status="PUBLISHED",
            created_by_admin_id=admin.id,
            published_at=now_utc(),
        )
        db.add(challenge)
        db.flush()
        db.add_all(
            [
                ModerationVideoORM(id="vid_1", challenge_id=challenge.id, author_user_id="mobile_user_1", url="https://cdn.challengehub.local/video/1", description="Відео-звіт 1", ai_status="REJECTED", status="PENDING_MANUAL", reports_count=1, views_count=124, likes_count=17, shares_count=5),
                ModerationVideoORM(id="vid_2", challenge_id=challenge.id, author_user_id="mobile_user_2", url="https://cdn.challengehub.local/video/2", description="Відео-звіт 2", ai_status="APPROVED", status="PUBLISHED", reports_count=4, is_ad=True, views_count=509, likes_count=66, shares_count=14),
            ]
        )
        db.add(ReportTicketORM(id="rep_1", video_id="vid_2", reason="Підозра на недоречний контент", status="OPEN"))
        db.add(AdVideoORM(id="ad_1", challenge_id=None, title="EVA Promo Intro", video_url="https://cdn.challengehub.local/ad/1"))
        db.add(PromoCodeORM(id=f"pc_{uuid4().hex[:10]}", challenge_id="sp_1", code="EVA-PARFUM-2026", is_sent=False))
        db.add(SystemSettingsORM(id="settings_main", ai_confidence_threshold=0.85, report_limit=3))
        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
