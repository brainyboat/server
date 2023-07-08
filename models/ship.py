from typing import Any

from pydantic import Field, validator

from models import BaseModel
from models.user import User

color_regex = r"^#(?i:[a-f0-9]{3}|[a-f0-9]{6})$"


class Ship(BaseModel):
    id: int
    imai: int
    course: list[tuple[float, float]] | None
    name: str
    color: str = Field(regex=color_regex)

    owner: User

    @validator("imai")
    def values_validator(
        cls,
        value: int,
        values: dict[str, Any],
        **kwargs: Any,
    ) -> int:
        assert len(str(value)) == 8, "The imai must be 8 digits"
        return value


class AddShip(BaseModel):
    imai: int
    name: str
    color: str = Field(regex=color_regex)

    @validator("imai")
    def values_validator(
        cls,
        value: int,
        values: dict[str, Any],
        **kwargs: Any,
    ) -> int:
        assert len(str(value)) == 8, "The imai must be 8 digits"
        return value
