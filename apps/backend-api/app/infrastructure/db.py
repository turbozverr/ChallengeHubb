from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, text
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
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MobileTokenORM(Base):
    __tablename__ = "mobile_auth_tokens"
    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
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
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("mobile_users.id"), nullable=False)
    challenge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VideoCommentORM(Base):
    __tablename__ = "video_comments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("moderation_videos.id"), nullable=False)
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
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)


class ModerationVideoORM(Base):
    __tablename__ = "moderation_videos"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    challenge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(32), default="SPONSORED")
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
    __table_args__ = (UniqueConstraint("user_id", "video_id", name="ux_video_likes_user_video"),)
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
            "ALTER TABLE moderation_videos ADD COLUMN challenge_type VARCHAR(32) DEFAULT 'SPONSORED'",
            "ALTER TABLE moderation_videos ADD COLUMN views_count INT DEFAULT 0",
            "ALTER TABLE moderation_videos ADD COLUMN likes_count INT DEFAULT 0",
            "ALTER TABLE moderation_videos ADD COLUMN shares_count INT DEFAULT 0",
            "CREATE TABLE IF NOT EXISTS video_likes (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, video_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE UNIQUE INDEX ux_video_likes_user_video ON video_likes (user_id, video_id)",
            "ALTER TABLE video_likes DROP FOREIGN KEY video_likes_ibfk_1",
            "ALTER TABLE video_likes DROP FOREIGN KEY fk_video_likes_video",
            "ALTER TABLE video_likes ADD CONSTRAINT fk_video_likes_video FOREIGN KEY (video_id) REFERENCES moderation_videos(id) ON DELETE CASCADE",
            "ALTER TABLE moderation_videos DROP FOREIGN KEY moderation_videos_ibfk_1",
            "CREATE TABLE IF NOT EXISTS promo_codes (id VARCHAR(64) PRIMARY KEY, challenge_id VARCHAR(64) NOT NULL, code VARCHAR(255) NOT NULL, is_sent BOOLEAN DEFAULT FALSE)",
            "CREATE TABLE IF NOT EXISTS ad_videos (id VARCHAR(64) PRIMARY KEY, challenge_id VARCHAR(64) NULL, title VARCHAR(255) NOT NULL, video_url TEXT NULL, file_path TEXT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS system_settings (id VARCHAR(64) PRIMARY KEY, ai_confidence_threshold FLOAT DEFAULT 0.85, report_limit INT DEFAULT 3)",
            "CREATE TABLE IF NOT EXISTS mobile_users (id VARCHAR(64) PRIMARY KEY, username VARCHAR(64) NOT NULL UNIQUE, full_name VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, avatar_url TEXT NULL, bio TEXT NULL, xp INT DEFAULT 0, is_premium BOOLEAN DEFAULT FALSE, status VARCHAR(32) DEFAULT 'ACTIVE', created_at DATETIME NULL, last_active_at DATETIME NULL)",
            "ALTER TABLE mobile_users ADD COLUMN fcm_token TEXT NULL",
            "CREATE TABLE IF NOT EXISTS mobile_auth_tokens (token VARCHAR(128) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS user_challenges (id VARCHAR(64) PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, difficulty VARCHAR(16) DEFAULT 'normal', duration_days INT DEFAULT 7, xp_reward INT DEFAULT 100, created_by_user_id VARCHAR(64) NOT NULL, status VARCHAR(32) DEFAULT 'PUBLISHED', created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS challenge_participations (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, challenge_id VARCHAR(64) NOT NULL, challenge_type VARCHAR(32) NOT NULL, status VARCHAR(32) DEFAULT 'ACTIVE', started_at DATETIME NULL, completed_at DATETIME NULL)",
            "CREATE UNIQUE INDEX ux_participation_user_challenge ON challenge_participations (user_id, challenge_id, challenge_type)",
            "CREATE TABLE IF NOT EXISTS video_comments (id VARCHAR(64) PRIMARY KEY, video_id VARCHAR(64) NOT NULL, user_id VARCHAR(64) NOT NULL, text TEXT NOT NULL, created_at DATETIME NULL)",
            "ALTER TABLE video_comments ADD COLUMN likes_count INT DEFAULT 0",
            "CREATE TABLE IF NOT EXISTS video_comment_likes (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, comment_id VARCHAR(64) NOT NULL, created_at DATETIME NULL)",
            "CREATE UNIQUE INDEX ux_video_comment_likes_user_comment ON video_comment_likes (user_id, comment_id)",
            "CREATE TABLE IF NOT EXISTS user_badges (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, badge_code VARCHAR(64) NOT NULL, title VARCHAR(255) NOT NULL, description TEXT NOT NULL, is_pinned BOOLEAN DEFAULT FALSE, created_at DATETIME NULL)",
            "CREATE TABLE IF NOT EXISTS notifications (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64) NOT NULL, title VARCHAR(255) NOT NULL, body TEXT NOT NULL, is_read BOOLEAN DEFAULT FALSE, created_at DATETIME NULL)",
            "ALTER TABLE ad_videos ADD COLUMN file_path TEXT NULL",
            "ALTER TABLE ad_videos MODIFY COLUMN challenge_id VARCHAR(64) NULL",
            "ALTER TABLE ad_videos MODIFY COLUMN video_url TEXT NULL",
            "UPDATE mobile_users SET email = 'user@challengehub.dev' WHERE email = 'user@challengehub.local'",
        ]
        for statement in migrations:
            try:
                conn.execute(text(statement))
            except Exception:
                pass
    with SessionLocal() as db:
        if db.query(WebUserORM).count() > 0:
            if db.query(MobileUserORM).count() == 0:
                db.add(
                    MobileUserORM(
                        id="mobile_user_1",
                        username="demo_user",
                        full_name="Demo User",
                        email="user@challengehub.dev",
                        password="user123",
                        bio="Demo ChallengeHub participant",
                        xp=420,
                        is_premium=False,
                        status="ACTIVE",
                        last_active_at=now_utc(),
                    )
                )
                db.add(UserBadgeORM(id="badge_1", user_id="mobile_user_1", badge_code="first_video", title="First Video", description="Uploaded first challenge video", is_pinned=True))
                db.commit()
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
        mobile_user = MobileUserORM(
            id="mobile_user_1",
            username="demo_user",
            full_name="Demo User",
            email="user@challengehub.dev",
            password="user123",
            bio="ÐŸÐµÑ€ÑˆÐ¸Ð¹ ÑƒÑ‡Ð°ÑÐ½Ð¸Ðº ChallengeHub",
            xp=420,
            is_premium=False,
            status="ACTIVE",
            last_active_at=now_utc(),
        )
        db.add(mobile_user)
        db.add(UserBadgeORM(id="badge_1", user_id=mobile_user.id, badge_code="first_video", title="First Video", description="Uploaded first challenge video", is_pinned=True))
        db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
