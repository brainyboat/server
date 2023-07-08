from datetime import datetime

from models import BaseModel


class Telemetry(BaseModel):
    id: int
    ship_id: int
    datetime: datetime
    longitude: float
    latitude: float
    angle: float
    temperature: float
    voltage: float
    velocity: float


class AddTelemetry(BaseModel):
    ship_id: int
    datetime: datetime
    longitude: float
    latitude: float
    angle: float
    temperature: float
    voltage: float
    velocity: float
