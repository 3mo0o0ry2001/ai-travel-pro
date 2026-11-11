import hmac
import logging
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from database import LimitExceeded, Store
from main import interpret_trip
from models import (
    AlertInput,
    Credentials,
    EmailInput,
    InterpretInput,
    ResetInput,
    SearchQuery,
    TokenInput,
    today_uae,
)
from security import (
    csrf_token,
    digest_token,
    hash_password,
    valid_csrf,
    verify_password,
)
from settings import Settings
from tools import ProviderError, search_flights

logger = logging.getLogger("waypoint")
ROOT = Path(__file__).parent


def create_app(settings=None):
    config = (settings or Settings.from_env()).validate()
    store = Store(config.database_path)
    session_cookie = "__Host-waypoint_session" if config.production else "waypoint_session"
    csrf_cookie = "__Host-waypoint_csrf" if config.production else "waypoint_csrf"
    dummy_password_hash = hash_password("unused-password-for-timing")

    @asynccontextmanager
    async def lifespan(application):
        store.initialize()
        yield

    application = FastAPI(
        title="Waypoint Travel",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if config.production else "/docs",
        redoc_url=None,
    )
    application.state.settings = config
    application.state.store = store
    hostname = urlsplit(config.base_url).hostname
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[hostname, "localhost", "127.0.0.1", "testserver"]
        if not config.production
        else [hostname],
    )

    @application.middleware("http")
    async def security_boundary(request, call_next):
        started = time.monotonic()
        request_id = secrets.token_hex(8)
        if config.production and request.url.scheme != "https":
            return JSONResponse({"detail": "HTTPS is required"}, status_code=400)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 16384:
                    return JSONResponse({"detail": "Request body is too large"}, status_code=413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
            token = request.headers.get("x-csrf-token", "")
            cookie = request.cookies.get(csrf_cookie, "")
            origin = request.headers.get("origin")
            allowed_origin = config.base_url if config.production else str(request.base_url).rstrip("/")
            if (origin and origin != allowed_origin) or not (
                hmac.compare_digest(token, cookie) and valid_csrf(token, config.secret)
            ):
                return JSONResponse(
                    {"detail": "Session check failed. Refresh this page and try again."}, status_code=403
                )
        response = await call_next(request)
        response.headers.update(
            {
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            }
        )
        if request.url.path.startswith("/api") or request.url.path == "/":
            response.headers["Cache-Control"] = "no-store"
        if config.production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        logger.info(
            "request id=%s method=%s path=%s status=%s ms=%d",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            int((time.monotonic() - started) * 1000),
        )
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [
            {"field": ".".join(map(str, entry["loc"][1:])), "message": entry["msg"]} for entry in exc.errors()
        ]
        return JSONResponse(
            {"detail": "Please check the highlighted fields.", "errors": errors}, status_code=422
        )

    @application.exception_handler(LimitExceeded)
    async def limit_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=429, headers={"Retry-After": "60"})

    @application.exception_handler(ProviderError)
    async def provider_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=503)

    @application.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logger.error("Unexpected failure type=%s path=%s", type(exc).__name__, request.url.path)
        return JSONResponse({"detail": "Something went wrong. Please try again later."}, status_code=500)

    def current_user(request: Request):
        user = store.session_user(request.cookies.get(session_cookie, ""))
        if not user:
            raise HTTPException(401, "Sign in to continue.")
        return dict(user)

    def limit_ip(request, action, maximum=10):
        peer = request.client.host if request.client else "unknown"
        store.limit(f"ip:{action}:{digest_token(peer)}", maximum, 900)

    def set_session(response, token):
        response.set_cookie(
            session_cookie,
            token,
            max_age=86400,
            httponly=True,
            secure=config.production,
            samesite="lax",
            path="/",
        )

    @application.get("/")
    def index():
        return FileResponse(ROOT / "static/index.html")

    @application.get("/health/live")
    def live():
        return {"status": "alive"}

    @application.get("/health/ready")
    def ready():
        try:
            with store.connect() as conn:
                conn.execute("SELECT 1 FROM users LIMIT 1")
            checks = {
                "database": True,
                "flights": config.provider == "demo" or bool(config.serp_api_key),
                "worker": store.worker_alive(),
                "mail": bool(config.smtp_host),
            }
        except sqlite3.Error:
            checks = {"database": False}
        healthy = all(checks.values())
        return JSONResponse(
            {"status": "ready" if healthy else "degraded", "checks": checks},
            status_code=200 if healthy else 503,
        )

    @application.get("/api/session")
    def session(request: Request):
        token = request.cookies.get(csrf_cookie, "")
        if not valid_csrf(token, config.secret):
            token = csrf_token(config.secret)
        user = store.session_user(request.cookies.get(session_cookie, ""))
        response = JSONResponse(
            {
                "user": dict(user) if user else None,
                "csrf": token,
                "demo": config.provider == "demo",
                "ai_available": bool(config.openai_api_key),
                "search_available": config.provider == "demo" or bool(config.serp_api_key),
                "email_delivery": "smtp" if config.smtp_host else "local-outbox",
                "today": today_uae().isoformat(),
                "alert_interval_hours": config.alert_interval // 3600,
            }
        )
        response.set_cookie(
            csrf_cookie, token, httponly=True, secure=config.production, samesite="strict", path="/"
        )
        return response

    @application.post("/api/auth/register", status_code=202)
    def register(credentials: Credentials, request: Request):
        limit_ip(request, "register", 5)
        password_hash = hash_password(credentials.password)
        try:
            user_id = store.create_user(str(credentials.email), password_hash)
        except sqlite3.IntegrityError:
            return {
                "message": "If this email is new, a verification message will arrive shortly. You can now sign in."
            }
        store.issue_email(user_id, "verify", config.base_url)
        return {
            "message": "If this email is new, a verification message will arrive shortly. You can now sign in."
        }

    @application.post("/api/auth/login")
    def login(credentials: Credentials, request: Request):
        limit_ip(request, "login")
        store.limit("login:" + digest_token(str(credentials.email)), 10, 900)
        user = store.user_by_email(str(credentials.email))
        # Hashing the same work factor prevents a missing user from becoming a timing oracle.
        expected = user["password_hash"] if user else dummy_password_hash
        valid = verify_password(credentials.password, expected)
        if not user or not valid:
            raise HTTPException(401, "Email or password is incorrect.")
        store.delete_session(request.cookies.get(session_cookie, ""))
        response = JSONResponse({"message": "Signed in."})
        set_session(response, store.new_session(user["id"]))
        return response

    @application.post("/api/auth/logout")
    def logout(request: Request):
        store.delete_session(request.cookies.get(session_cookie, ""))
        response = JSONResponse({"message": "Signed out."})
        response.delete_cookie(
            session_cookie, path="/", secure=config.production, httponly=True, samesite="lax"
        )
        return response

    @application.post("/api/auth/verify")
    def verify(payload: TokenInput, request: Request):
        limit_ip(request, "token", 20)
        if not store.consume_token(payload.token, "verify"):
            raise HTTPException(400, "This verification link is invalid or has expired.")
        return {"message": "Email verified. You can now create price alerts."}

    @application.post("/api/auth/resend", status_code=202)
    def resend(user=Depends(current_user)):
        store.limit(f"verify:{user['id']}", 3, 3600)
        if not user["verified"]:
            store.issue_email(user["id"], "verify", config.base_url)
        return {"message": "Verification email queued. Check your inbox shortly."}

    @application.post("/api/auth/forgot", status_code=202)
    def forgot(payload: EmailInput, request: Request):
        limit_ip(request, "forgot", 5)
        store.limit("forgot:" + digest_token(str(payload.email).lower()), 3, 3600)
        user = store.user_by_email(str(payload.email))
        if user:
            store.issue_email(user["id"], "reset", config.base_url)
        return {"message": "If this account exists, a reset email will arrive shortly."}

    @application.post("/api/auth/reset")
    def reset(payload: ResetInput, request: Request):
        limit_ip(request, "token", 20)
        if not store.consume_token(payload.token, "reset", hash_password(payload.password)):
            raise HTTPException(400, "This reset link is invalid or has expired.")
        return {"message": "Password changed. Sign in again."}

    @application.delete("/api/account")
    def delete_account(user=Depends(current_user)):
        store.delete_user(user["id"])
        response = JSONResponse({"message": "Your account and saved alerts have been deleted."})
        response.delete_cookie(session_cookie, path="/")
        return response

    @application.post("/api/search")
    def search(query: SearchQuery, request: Request, user=Depends(current_user)):
        limit_ip(request, "search", 60)
        store.limit(f"search:{user['id']}", 30, 3600)
        return search_flights(query, config)

    @application.post("/api/interpret")
    def interpret(payload: InterpretInput, request: Request, user=Depends(current_user)):
        limit_ip(request, "ai", 20)
        store.limit(f"ai:{user['id']}", 5, 86400)
        store.limit("ai:global", 100, 86400)
        return interpret_trip(payload.text, config)

    @application.get("/api/alerts")
    def alerts(user=Depends(current_user)):
        return {"alerts": store.user_alerts(user["id"])}

    @application.post("/api/alerts", status_code=201)
    def create_alert(payload: AlertInput, user=Depends(current_user)):
        if not user["verified"]:
            raise HTTPException(403, "Verify your email before creating a price alert.")
        store.limit(f"alert:{user['id']}", 10, 3600)
        store.add_alert(user["id"], payload)
        return {"message": "Price alert saved. Checks run on the published schedule."}

    @application.delete("/api/alerts/{alert_id}")
    def delete_alert(alert_id: int, user=Depends(current_user)):
        if not store.remove_alert(user["id"], alert_id):
            raise HTTPException(404, "Alert not found.")
        return {"message": "Alert deleted."}

    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    return application
