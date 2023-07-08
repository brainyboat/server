import hashlib
from datetime import datetime
from typing import Self

import jwt
from pydantic import Field

from models import BaseModel
from settings import settings


class Auth(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)

    def get_password_hash(self, salt: str) -> str:
        return hashlib.sha512((self.password + salt).encode("UTF-8")).hexdigest()


class Token(BaseModel):
    id: int
    issued_at: datetime
    token: str

    @classmethod
    def create(
        cls,
        id: int,
        password_update_date: datetime,
    ) -> Self:
        return cls(
            id=id,
            issued_at=password_update_date,
            token=jwt.encode(
                {
                    "sub": id,
                    "iat": password_update_date.timestamp(),
                },
                settings.secret,
                "HS256",
            ),
        )


class User(BaseModel):
    id: int
    username: str = Field(min_length=3)


class UpdateUsername(BaseModel):
    username: str = Field(min_length=3)


class UpdatePassword(BaseModel):
    password: str = Field(min_length=8)

    def get_password_hash(self, salt: str) -> str:
        return hashlib.sha512((self.password + salt).encode("UTF-8")).hexdigest()
