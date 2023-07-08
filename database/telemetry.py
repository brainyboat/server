from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from database.ship import Ship


class Telemetry(Base):
    __tablename__ = "telemetry"
    id: Mapped[int] = mapped_column(primary_key=True)
    ship_id: Mapped[int] = mapped_column(ForeignKey(Ship.id, ondelete="CASCADE"))
    datetime: Mapped[datetime]
    longitude: Mapped[float]
    latitude: Mapped[float]
    angle: Mapped[float]
    temperature: Mapped[float]
    voltage: Mapped[float]
    velocity: Mapped[float]

    ship: Mapped[Ship] = relationship(lazy="joined")
