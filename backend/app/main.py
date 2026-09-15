from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev/test convenience only — production schema changes go through Alembic (§9.2).
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
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "message": "Validation failed", "data": exc.errors()},
    )


@app.get("/health")
async def health():
    return {"status": "success", "message": "SEES Nexus API is running", "data": None}


app.include_router(api_router)
