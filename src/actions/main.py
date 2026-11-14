from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from scalar_fastapi import get_scalar_api_reference

from src.actions.api.responses import ApiResponse
from src.actions.api.routers import router as api_router
from src.actions.infrastructure.config import get_settings
from src.actions.infrastructure.database import db_engine
from src.actions.infrastructure.logging_config import setup_logging

logger = logging.getLogger(__name__)

# -- setup the logger ---
setup_logging()


# --- lifespan handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Application startup completed")
        yield
    except Exception:
        logger.exception("Application lifecycle failed")
        raise
    finally:
        await db_engine.dispose()
        logger.info("Application shutdown completed")


# --- create app ---
app = FastAPI(
    title=get_settings().app.project_name,
    version=get_settings().app.version,
    lifespan=lifespan,
)


@app.get("/scalar", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


# --- exception handler ---


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception",
        extra={"status_code": exc.status_code, "path": request.url.path},
    )
    return ApiResponse.error(message=exc.detail, code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    logger.warning("Request validation failed", extra={"path": request.url.path})
    return ApiResponse.error(
        message="Validation failed",
        code=422,
        data=None,
        meta={
            "path": str(request.url),
            "errors": exc.errors(),
        },
    )


# --- imports routers ---
app.include_router(api_router)

