from asyncio import Queue

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from sqlalchemy import and_, select

import database
import models
from database.ship import Ship
from database.telemetry import Telemetry
from endpoints import dependencies

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])
telemetry_pool: dict[int, set[Queue[models.telemetry.Telemetry]]] = {}


@router.get("/get/id")
async def get_by_id(
    user: dependencies.HeaderUser, id: int
) -> models.telemetry.Telemetry:
    async with database.sessions.begin() as session:
        telemetry = await session.scalar(
            select(Telemetry)
            .join(Ship)
            .where(
                and_(
                    Telemetry.id == id,
                    Ship.owner_id == user.id,
                )
            )
        )

        if telemetry is None:
            raise HTTPException(404, "Telemetry not found")

        return models.telemetry.Telemetry.from_orm(telemetry)


@router.get("/get/my")
async def get_my(user: dependencies.HeaderUser) -> list[models.telemetry.Telemetry]:
    async with database.sessions.begin() as session:
        telemetry = await session.scalars(
            select(Telemetry).join(Ship).where(Ship.owner_id == user.id)
        )

        return [models.telemetry.Telemetry.from_orm(t) for t in telemetry]


@router.post("/add")
async def add(
    user: dependencies.HeaderUser,
    telemetry_model: models.telemetry.AddTelemetry,
) -> models.telemetry.Telemetry:
    async with database.sessions.begin() as session:
        if (
            await session.scalar(
                select(Ship).where(
                    and_(
                        Ship.id == telemetry_model.ship_id,
                        Ship.owner_id == user.id,
                    )
                )
            )
            is None
        ):
            raise HTTPException(404, "Ship not found")

        telemetry = Telemetry(
            ship_id=telemetry_model.ship_id,
            datetime=telemetry_model.datetime,
            longitude=telemetry_model.longitude,
            latitude=telemetry_model.latitude,
            angle=telemetry_model.angle,
            temperature=telemetry_model.temperature,
            voltage=telemetry_model.voltage,
            velocity=telemetry_model.velocity,
        )

        session.add(telemetry)
        await session.flush()
        await session.refresh(telemetry)

        if telemetry_model.ship_id in telemetry_pool:
            queue_telemetry_model = models.telemetry.Telemetry.from_orm(telemetry)
            for queue in telemetry_pool[telemetry_model.ship_id]:
                await queue.put(queue_telemetry_model)

        return models.telemetry.Telemetry.from_orm(telemetry)


@router.websocket("/listen/telemetry")
async def listen_telemetry(
    websocket: WebSocket,
    user: dependencies.QueryUser,
    id: int,
) -> None:
    await websocket.accept()

    if id not in telemetry_pool:
        telemetry_pool[id] = set()

    async with database.sessions.begin() as session:
        if (
            await session.scalar(
                select(Ship).where(
                    and_(
                        Ship.id == id,
                        Ship.owner_id == user.id,
                    )
                )
            )
            is None
        ):
            raise WebSocketException(1003, "Ship not found")

    queue: Queue[models.telemetry.Telemetry] = Queue()
    telemetry_pool[id].add(queue)

    try:
        while True:
            telemetry = await queue.get()
            await websocket.send_text(telemetry.json())
    except WebSocketDisconnect:
        telemetry_pool[id].remove(queue)
        if len(telemetry_pool[id]) == 0:
            telemetry_pool.pop(id)
        await websocket.close()
