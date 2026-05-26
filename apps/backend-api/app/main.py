import logging
import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.admin import router as admin_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.challenges import router as challenges_router
from app.api.routes.health import router as health_router
from app.api.routes.mobile import router as mobile_router
from app.api.routes.moderation import router as moderation_router
from app.api.routes.settings import router as settings_router
from app.api.routes.web_users import router as web_users_router
from app.core.config import settings
from app.infrastructure.db import init_db

app = FastAPI(title=settings.app_name, version=settings.app_version)
logger = logging.getLogger("challengehub.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
BUILD_ID = f"challengehub-web-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(web_users_router, prefix="/api/v1")
app.include_router(challenges_router, prefix="/api/v1")
app.include_router(moderation_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(mobile_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("=== Registered routes ===")
    for route in app.routes:
        methods = ",".join(sorted(getattr(route, "methods", []) or []))
        logger.info("%s %s", methods, getattr(route, "path", ""))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("REQ %s %s", request.method, request.url.path)
    response = await call_next(request)
    response.headers["X-ChallengeHub-Build"] = BUILD_ID
    logger.info("RES %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.error("Unhandled exception: %s\n%s", str(exc), traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {exc.__class__.__name__}: {str(exc)}"},
    )


@app.get("/api/v1/debug/routes")
def debug_routes() -> dict[str, list[dict[str, str]]]:
    payload: list[dict[str, str]] = []
    for route in app.routes:
        methods = ",".join(sorted(getattr(route, "methods", []) or []))
        payload.append({"path": getattr(route, "path", ""), "methods": methods})
    return {"build_id": BUILD_ID, "routes": payload}
