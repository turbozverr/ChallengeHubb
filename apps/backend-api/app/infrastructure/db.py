from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, create_engine, text
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


class MobileUserORM(Base):
    __tablename__ = "mobile_users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(32), default="password")
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_background: Mapped[str | None] = mapped_column(String(64), nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_comeback_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MobileTokenORM(Base):
    __tablename__ = "mobile_auth_tokens"
    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserIntegrationORM(Base):
    __tablename__ = "user_integrations"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="ux_user_integrations_user_provider"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class IntegrationStateORM(Base):
    __tablename__ = "integration_states"
    state: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserFollowORM(Base):
    __tablename__ = "user_follows"
    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="ux_user_follows_pair"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    follower_id: Mapped[str] = mapped_column(String(64), nullable=False)
    followed_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserChallengeORM(Base):
    __tablename__ = "user_challenges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default="normal")
    duration_days: Mapped[int] = mapped_column(Integer, default=7)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PUBLISHED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ChallengeParticipationORM(Base):
    __tablename__ = "challenge_participations"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", "challenge_type", name="ux_participation_user_challenge"),
        Index("ix_ch_participation_user_status_started", "user_id", "status", "started_at"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    challenge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VideoCommentORM(Base):
    __tablename__ = "video_comments"
    __table_args__ = (Index("ix_video_comments_video_created", "video_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class VideoCommentLikeORM(Base):
    __tablename__ = "video_comment_likes"
    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="ux_video_comment_likes_user_comment"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    comment_id: Mapped[str] = mapped_column(ForeignKey("video_comments.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UserBadgeORM(Base):
    __tablename__ = "user_badges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    badge_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class NotificationORM(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
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


class ModerationVideoORM(Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_author_created", "author_user_id", "created_at"),
        Index("ix_videos_status_created", "status", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    challenge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(32), default="SPONSORED")
    author_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_status: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reports_count: Mapped[int] = mapped_column(Integer, default=0)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    shares_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportTicketORM(Base):
    __tablename__ = "report_tickets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VideoLikeORM(Base):
    __tablename__ = "video_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="ux_video_likes_user_video"),
        Index("ix_video_likes_video_id", "video_id"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AdVideoORM(Base):
    __tablename__ = "ad_videos"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PUBLISHED")
    created_by_admin_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    shares_count: Mapped[int] = mapped_column(Integer, default=0)
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
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        data[column.name] = value.isoformat() if isinstance(value, datetime) else value
    return data


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        migrations = [
            "CREATE TABLE IF NOT EXISTS web_users (id VARCHAR(64) PRIMARY KEY, full_name VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE, role VARCHAR(32) NOT NULL, password VARCHAR(255) NOT NULL, company_name VARCHAR(255) NULL, is_active BOOLEAN DEFAULT TRUE, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS auth_tokens (token VARCHAR(128) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS mobile_users (id VARCHAR(64) PRIMARY KEY, username VARCHAR(64) NOT NULL UNIQUE, full_name VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, auth_provider VARCHAR(32) DEFAULT 'password', avatar_url TEXT NULL, profile_background VARCHAR(64) NULL, xp INT DEFAULT 0, is_premium BOOLEAN DEFAULT FALSE, fcm_token TEXT NULL, status VARCHAR(32) DEFAULT 'ACTIVE', created_at DATETIME NULL, last_active_at DATETIME NULL, last_comeback_notified_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS mobile_auth_tokens (token VARCHAR(128) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS user_integrations (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, provider VARCHAR(32) NOT NULL, external_account_name VARCHAR(255) NULL, access_token TEXT NULL, refresh_token TEXT NULL, token_expires_at DATETIME NULL, created_at DATETIME NULL, updated_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS integration_states (state VARCHAR(128) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, provider VARCHAR(32) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS user_follows (id VARCHAR(64) PRIMARY KEY, follower_id VARCHAR(64) NOT NULL, followed_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS sponsored_challenges (id VARCHAR(64) PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, reward_text VARCHAR(255) NOT NULL, difficulty VARCHAR(16) DEFAULT 'normal', duration_days INT DEFAULT 7, xp_reward INT DEFAULT 100, promo_mode VARCHAR(32) DEFAULT 'SINGLE', promo_single_code VARCHAR(255) NULL, client_id VARCHAR(64) NOT NULL, client_company_name VARCHAR(255) NOT NULL, status VARCHAR(32) NOT NULL, created_by_admin_id VARCHAR(64) NOT NULL, created_at DATETIME NULL, published_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS promo_codes (id VARCHAR(64) PRIMARY KEY, challenge_id VARCHAR(64) NOT NULL, code VARCHAR(255) NOT NULL)",
            "CREATE TABLE IF NOT EXISTS user_challenges (id VARCHAR(64) PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, difficulty VARCHAR(16) DEFAULT 'normal', duration_days INT DEFAULT 7, xp_reward INT DEFAULT 100, created_by_user_id VARCHAR(64) NOT NULL, status VARCHAR(32) DEFAULT 'PUBLISHED', created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS challenge_participations (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, challenge_id VARCHAR(64) NOT NULL, challenge_type VARCHAR(32) NOT NULL, status VARCHAR(32) DEFAULT 'ACTIVE', started_at DATETIME NULL, completed_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS videos (id VARCHAR(64) PRIMARY KEY, challenge_id VARCHAR(64) NOT NULL, challenge_type VARCHAR(32) DEFAULT 'SPONSORED', author_user_id VARCHAR(64) NOT NULL, url TEXT NOT NULL, description TEXT NULL, ai_reason TEXT NULL, ai_confidence FLOAT NULL, ai_status VARCHAR(32) NOT NULL, status VARCHAR(32) NOT NULL, reports_count INT DEFAULT 0, views_count INT DEFAULT 0, shares_count INT DEFAULT 0, created_at DATETIME NULL, decided_by VARCHAR(64) NULL, decided_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS report_tickets (id VARCHAR(64) PRIMARY KEY, video_id VARCHAR(64) NOT NULL, reason TEXT NOT NULL, status VARCHAR(32) NOT NULL, created_at DATETIME NULL, decided_by VARCHAR(64) NULL, decided_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS video_likes (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, video_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS video_comments (id VARCHAR(64) PRIMARY KEY, video_id VARCHAR(64) NOT NULL, user_id VARCHAR(64) NOT NULL, text TEXT NOT NULL, likes_count INT DEFAULT 0, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS video_comment_likes (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, comment_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS user_badges (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, badge_code VARCHAR(64) NOT NULL, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, is_pinned BOOLEAN DEFAULT FALSE, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS notifications (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, title VARCHAR(255) NOT NULL, body TEXT NOT NULL, is_read BOOLEAN DEFAULT FALSE, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS ad_videos (id VARCHAR(64) PRIMARY KEY, description TEXT NULL, url TEXT NULL, file_path TEXT NULL, status VARCHAR(32) DEFAULT 'PUBLISHED', created_by_admin_id VARCHAR(64) NULL, views_count INT DEFAULT 0, likes_count INT DEFAULT 0, shares_count INT DEFAULT 0, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS system_settings (id VARCHAR(64) PRIMARY KEY, ai_confidence_threshold FLOAT DEFAULT 0.85, report_limit INT DEFAULT 3)",
            "CREATE UNIQUE INDEX ux_video_likes_user_video ON video_likes (user_id, video_id)",
            "CREATE UNIQUE INDEX ux_video_comment_likes_user_comment ON video_comment_likes (user_id, comment_id)",
            "CREATE UNIQUE INDEX ux_user_integrations_user_provider ON user_integrations (user_id, provider)",
            "CREATE UNIQUE INDEX ux_user_follows_pair ON user_follows (follower_id, followed_id)",
            "CREATE UNIQUE INDEX ux_participation_user_challenge ON challenge_participations (user_id, challenge_id, challenge_type)",
            "CREATE INDEX ix_videos_author_created ON videos (author_user_id, created_at)",
            "CREATE INDEX ix_videos_status_created ON videos (status, created_at)",
            "CREATE INDEX ix_ch_participation_user_status_started ON challenge_participations (user_id, status, started_at)",
            "CREATE INDEX ix_video_comments_video_created ON video_comments (video_id, created_at)",
            "CREATE INDEX ix_notifications_user_read_created ON notifications (user_id, is_read, created_at)",
            "CREATE INDEX ix_video_likes_video_id ON video_likes (video_id)",
        ]
        for statement in migrations:
            try:
                conn.execute(text(statement))
            except Exception:
                pass
    with SessionLocal() as db:
        if db.query(WebUserORM).count() > 0:
            return
        admin = WebUserORM(id="w_admin_1", full_name="Admin ChallengeHub", email="admin@challengehub.dev", role=WebRole.ADMIN.value, password="12345")
        db.add(admin)
        db.add(SystemSettingsORM(id="settings_main", ai_confidence_threshold=0.85, report_limit=3))
        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

