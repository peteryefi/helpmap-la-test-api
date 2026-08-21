"""FastAPI entrypoint: app instance, CORS, rate limiting, routers."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import init_db
from app.ratelimit import limiter
from app.routers import reports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Helpmap Reports API",
    description=(
        "Testbed API for browser-submitted disaster reports (Data Flow 1). "
        "Replaces the browser-local/localStorage design with a shared "
        "backend so reports persist and are visible across users."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(reports.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
