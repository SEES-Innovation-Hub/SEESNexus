from fastapi import APIRouter

from app.api.v1 import admin, auth, notify, projects

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(notify.router)
api_router.include_router(admin.router)
api_router.include_router(projects.router)
