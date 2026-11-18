from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A zero-setup SQLite dev database gets its tables made here. Postgres is
    # managed by Alembic only: create_all there would build tables Alembic then
    # trips over, and would never add new columns anyway.
    if settings.is_sqlite:
        await init_models()
    yield


app = FastAPI(title="SEES Nexus API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Wrap every error in the standard {status, message, data} envelope (Tech Doc §5, §10).
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail, "data": None},
        # Keeps Retry-After on 429s and WWW-Authenticate on 401s.
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Validation failed", "data": exc.errors()},
    )


@app.get("/health")
async def health():
    return {"status": "success", "message": "SEES Nexus API is running", "data": None}


app.include_router(api_router)
