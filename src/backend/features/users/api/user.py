from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database.db_helper import db_helper
from features.users.models.user import User
from features.users.schemas.user import (
    UserLoginSchema,
    UserRegisterSchema,
    UserResponseSchema,
)
from features.users.service.user import (
    get_current_user_from_cookie,
    login_user_service,
    register_user_service,
)

router = APIRouter()


@router.post(
    "/signup",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserRegisterSchema,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
):
    new_user = await register_user_service(session, user_data)

    return new_user


@router.post("/login", response_model=UserResponseSchema)
async def login_for_access_token(
    response: Response,
    login_data: UserLoginSchema,
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
):
    user_schema, access_token = await login_user_service(session, login_data)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.jwt.access_token_lifetime_seconds,
    )
    return user_schema


@router.get("/me", response_model=UserResponseSchema)
async def read_users_me(current_user: User = Depends(get_current_user_from_cookie)):
    return UserResponseSchema(
        user_id=current_user.id,
        email=current_user.email,
    )
