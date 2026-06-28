from fastapi import APIRouter

from core.config import settings
from features.chats.api.chat import router as chat_router
from features.messages.api.message import router as message_router
from features.users.api.user import router as users_router


router = APIRouter(
    prefix=settings.api.v1.prefix,
)

router.include_router(
    router=chat_router,
    tags=[settings.api.v1.chats[1:].capitalize()],
    prefix=settings.api.v1.chats,
)

router.include_router(
    router=message_router,
    tags=[settings.api.v1.messages[1:].capitalize()],
    prefix=settings.api.v1.messages,
)

router.include_router(
    router=users_router,
    tags=[settings.api.v1.users[1:].capitalize()],
    prefix=settings.api.v1.users,
)
