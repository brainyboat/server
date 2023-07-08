from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from database.user import User


class Ship(Base):
    __tablename__ = "ships"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            User.id,
            ondelete="CASCADE",
        )
    )
    imai: Mapped[int] = mapped_column(unique=True)
    course: Mapped[list | None] = mapped_column(JSON, default=None)
    name: Mapped[str]
    color: Mapped[str]

    owner: Mapped[User] = relationship(lazy="joined")
