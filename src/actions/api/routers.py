from fastapi import APIRouter

from src.actions.events.routers import router as event_router

router = APIRouter()

router.include_router(event_router)
