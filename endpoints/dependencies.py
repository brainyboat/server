from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select

import database
from database.user import User as DatabaseUser
from settings import settings


async def get_user(token: str) -> DatabaseUser:
    try:
        data: dict = jwt.decode(token, settings.secret, algorithms=["HS256"])
        user_id = int(data["sub"])
        issued_at = float(data["iat"])
    except (jwt.DecodeError, ValueError):
        raise HTTPException(401, "The token is invalid")

    async with database.sessions.begin() as session:
        user = await session.scalar(
            select(DatabaseUser).where(DatabaseUser.id == user_id)
        )

        if user is None or user.password_update_date.timestamp() != issued_at:
            raise HTTPException(401, "The token is invalid")

        session.expunge(user)
        return user


async def header_user(token: Annotated[str, Header(alias="X-Token")]) -> DatabaseUser:
    return await get_user(token)


async def query_user(token: str) -> DatabaseUser:
    return await header_user(token)


HeaderUser = Annotated[DatabaseUser, Depends(header_user, use_cache=True)]
QueryUser = Annotated[DatabaseUser, Depends(query_user, use_cache=True)]
