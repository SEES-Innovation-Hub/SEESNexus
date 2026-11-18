from fastapi import APIRouter

from app.api.v1 import admin, articles, auth, events, hardware, notify, projects, upload, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(notify.router)
api_router.include_router(admin.router)
api_router.include_router(projects.router)
api_router.include_router(hardware.router)
api_router.include_router(events.router)
api_router.include_router(articles.router)
api_router.include_router(users.router)
api_router.include_router(upload.router)
