import logging
from http import HTTPStatus

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router as api_router
from core.config import settings


def _init_sentry() -> None:
    """Initialise Sentry only when a DSN is configured. The import is lazy so the
    app runs fine without the optional dependency installed."""
    if not settings.sentry.dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry.dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
        )
    except Exception:  # noqa: BLE001 — observability must never block startup
        logging.getLogger("agent").warning("sentry_init_failed")


_init_sentry()

app = FastAPI(
    title="AlfaFuture — Small Business Assistant",
    docs_url="/docs" if settings.environment != "prod" else None,
    redoc_url="/redoc" if settings.environment != "prod" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get(
    "/ping",
    status_code=HTTPStatus.OK,
)
async def ping():
    return {"message": "pong"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.environment == "dev",
    )
