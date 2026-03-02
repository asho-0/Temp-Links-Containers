from fastapi import FastAPI

from app.api import api_router
from app.api.auth import auth_router
from app.db.session import db_lifespan
from fastapi.exceptions import HTTPException, RequestValidationError
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Zero-Knowledge Secrets API", lifespan=db_lifespan)

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router)
    app.include_router(auth_router)

    return app


app = create_app()

if __name__ == "__main__":
    settings.setup_logging()
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.FAST_API_DEBUG,
        log_level="debug" if settings.FAST_API_DEBUG else "info",
    )
