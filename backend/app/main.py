import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import ai, auth, billing, projects

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

app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(projects.router)
app.include_router(billing.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
