from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import db_helper
from features.users.models.user import User
from features.users.schemas.user import (
    UserLoginSchema,
    UserRegisterSchema,
    UserResponseSchema,
)
from utils.JWT import create_access_token, decode_jwt, hash_password, validate_password


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def register_user_service(
    session: AsyncSession, user_data: UserRegisterSchema
) -> UserResponseSchema:
    existing_user = await get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        surname=user_data.surname,
        patronymic=user_data.patronymic,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    user_schema = UserResponseSchema.model_validate(
        {"user_id": new_user.id, "email": new_user.email}
    )

    return user_schema


async def login_user_service(
    session: AsyncSession, login_data: UserLoginSchema
) -> tuple[UserResponseSchema, str]:
    user = await get_user_by_email(session, login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not validate_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=user.id,
        user_email=user.email,
    )

    user_schema = UserResponseSchema.model_validate(
        {"user_id": user.id, "email": user.email}
    )

    return user_schema, access_token


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user_from_cookie(
    session: AsyncSession = Depends(db_helper.dependency_session_getter),
    access_token: str | None = Cookie(None),
) -> User:
    if access_token is None:
        raise CREDENTIALS_EXCEPTION
    try:
        payload = decode_jwt(token=access_token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CREDENTIALS_EXCEPTION

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise CREDENTIALS_EXCEPTION

    user = await get_user_by_id(session, int(user_id))
    if user is None:
        raise CREDENTIALS_EXCEPTION

    return user
