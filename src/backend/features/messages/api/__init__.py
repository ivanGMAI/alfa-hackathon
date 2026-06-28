from fastapi import APIRouter

from .message import router as message_router

router = APIRouter()

router.include_router(router=message_router)
