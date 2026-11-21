import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from quorum.api.routes import router
from quorum.config import settings
from quorum.engine import ExpertStore, get_gemini_adapter

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
logger = logging.getLogger("quorum.api.main")


class TokenBucketRateLimiter:
    """In-memory rate limiter protecting LLM endpoints from automated denial-of-service."""

    def __init__(self, capacity: int = 20, refill_per_sec: float = 0.33):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens: Dict[str, float] = defaultdict(lambda: float(capacity))
        self.last_update: Dict[str, float] = defaultdict(time.time)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        elapsed = now - self.last_update[client_ip]
        self.last_update[client_ip] = now
        self.tokens[client_ip] = min(
            self.capacity, self.tokens[client_ip] + elapsed * self.refill_per_sec
        )

        if self.tokens[client_ip] >= 1.0:
            self.tokens[client_ip] -= 1.0
            return True
        return False


rate_limiter = TokenBucketRateLimiter(capacity=20, refill_per_sec=0.33)


class SecurityAndCacheMiddleware(BaseHTTPMiddleware):
    """Enforces WCAG & OWASP security headers, gzip, and static asset caching."""

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Rate limit heavy LLM / generation endpoints
        if request.url.path in (
            "/api/council/evaluate",
            "/api/council/evaluate/stream",
            "/api/rebut",
            "/api/council/expert-chat",
        ):
            if not rate_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "RateLimitExceeded",
                        "detail": "Evaluation rate limit reached (20 requests/minute). Please allow a moment before next submission.",
                    },
                )

        response = await call_next(request)

        # OWASP Security Headers
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"

        # Cache-Control for static assets
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=3600"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup banner with mode reporting
    store = ExpertStore.get_instance()
    adapter = get_gemini_adapter()
    mode = "LIVE (Google Gemini API)" if adapter._is_ready else "OFFLINE (Heuristic Simulation)"

    print("===============================================================================")
    print(f"  {settings.app_name} v{settings.app_version}")
    print(f"  Mode:           {mode}")
    print(f"  Local URL:      http://{settings.host}:{settings.port}")
    print(
        f"  Loaded Experts: {store.count()} personas ({len(store._deep_profile_ids)} deep dossiers)"
    )
    print("===============================================================================")
    yield
    print(f"[{settings.app_name}] Server stopped.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend engine for Quorum (Expert Council) - AI startup evaluation platform.",
    debug=settings.debug,
    lifespan=lifespan,
)

# Compression & Security Middleware
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SecurityAndCacheMiddleware)

# CORS Middleware (Localhost only, credentials disabled)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not origins:
    origins = ["http://localhost:8000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Standardized JSON error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "RequestError",
            "detail": exc.detail,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"error": "ValidationError", "detail": str(exc)})


app.include_router(router)

# Mount static files and root route
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def root_index():
        return FileResponse(STATIC_DIR / "index.html")
