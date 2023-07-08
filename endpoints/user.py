import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

import database
import models
from database.user import User
from endpoints import dependencies

router = APIRouter(prefix="/user", tags=["Users"])


@router.post("/register")
async def register(auth: models.user.Auth) -> models.user.Token:
    async with database.sessions.begin() as session:
        if (
            await session.scalar(select(User).where(User.username == auth.username))
            is not None
        ):
            raise HTTPException(409, "User with this username already exists")

        salt = secrets.token_hex(8)
        password_updated_date = datetime.utcnow()
        user = User(
            username=auth.username,
            password=auth.get_password_hash(salt),
            password_update_date=password_updated_date,
            salt=salt,
        )

        session.add(user)
        await session.flush()

        return models.user.Token.create(
            user.id,
            user.password_update_date,
        )


@router.post("/login")
async def login(auth: models.user.Auth) -> models.user.Token:
    async with database.sessions.begin() as session:
        user = await session.scalar(select(User).where(User.username == auth.username))

        if user is None or user.password != auth.get_password_hash(user.salt):
            raise HTTPException(401, "The username or password is incorrect")

        return models.user.Token.create(
            user.id,
            user.password_update_date,
        )


@router.get("/me")
async def me(user: dependencies.HeaderUser) -> models.user.User:
    return models.user.User.from_orm(user)


@router.get("/get/id")
async def get_by_id(id: int) -> models.user.User:
    async with database.sessions.begin() as session:
        user = await session.scalar(select(User).where(User.id == id))

        if user is None:
            raise HTTPException(404, "User not found")

        return models.user.User.from_orm(user)


@router.get("/get/username")
async def get_by_username(username: str) -> models.user.User:
    async with database.sessions.begin() as session:
        user = await session.scalar(select(User).where(User.username == username))

        if user is None:
            raise HTTPException(404, "User not found")

        return models.user.User.from_orm(user)


@router.put("/update/username")
async def update_username(
    user: dependencies.HeaderUser,
    update: models.user.UpdateUsername,
) -> models.user.User:
    async with database.sessions.begin() as session:
        session.add(user)

        if (
            await session.scalar(select(User).where(User.username == update.username))
            is not None
        ):
            raise HTTPException(409, "User with this username already exists")

        user.username = update.username
        return models.user.User.from_orm(user)


@router.put("/update/password")
async def update_password(
    user: dependencies.HeaderUser,
    update: models.user.UpdatePassword,
) -> models.user.Token:
    async with database.sessions.begin() as session:
        session.add(user)

        user.salt = secrets.token_hex(8)
        user.password = update.get_password_hash(user.salt)
        user.password_update_date = datetime.utcnow()

        return models.user.Token.create(
            user.id,
            user.password_update_date,
        )


@router.delete("/delete")
async def delete(user: dependencies.HeaderUser) -> models.user.User:
    async with database.sessions.begin() as session:
        await session.delete(user)
        return models.user.User.from_orm(user)
