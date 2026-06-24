import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.2)

app = FastAPI(title="Staqk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://staqk.com",
        "https://*.staqk.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers registered here as they are built
# from app.routers import auth, projects, ai, payments, public
# app.include_router(auth.router, prefix="/auth")
# app.include_router(projects.router, prefix="/projects")
# app.include_router(ai.router, prefix="/ai")
# app.include_router(payments.router, prefix="/payments")
# app.include_router(public.router, prefix="/public")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
