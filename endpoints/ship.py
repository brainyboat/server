import json
from asyncio import Queue

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from sqlalchemy import and_, delete, select

import database
import models
from database.ship import Ship
from database.telemetry import Telemetry
from endpoints import dependencies

router = APIRouter(prefix="/ship", tags=["Ships"])
course_pool: dict[int, Queue[list[tuple[float, float]] | None]] = {}


@router.get("/get/id")
async def get_by_id(user: dependencies.HeaderUser, id: int) -> models.ship.Ship:
    async with database.sessions.begin() as session:
        ship = await session.scalar(
            select(Ship).where(
                and_(
                    Ship.id == id,
                    Ship.owner_id == user.id,
                )
            )
        )

        if ship is None:
            raise HTTPException(404, "Ship not found")

        return models.ship.Ship.from_orm(ship)


@router.get("/get/imai")
async def get_by_imai(user: dependencies.HeaderUser, imai: int) -> models.ship.Ship:
    async with database.sessions.begin() as session:
        ship = await session.scalar(
            select(Ship).where(
                and_(
                    Ship.imai == imai,
                    Ship.owner_id == user.id,
                )
            )
        )

        if ship is None:
            raise HTTPException(404, "Ship not found")

        return models.ship.Ship.from_orm(ship)


@router.get("/get/my")
async def get_my(user: dependencies.HeaderUser) -> list[models.ship.Ship]:
    async with database.sessions.begin() as session:
        ships = await session.scalars(select(Ship).where(Ship.owner_id == user.id))
        return [models.ship.Ship.from_orm(ship) for ship in ships]


@router.get("/get/telemetry")
async def get_telemetry(
    user: dependencies.HeaderUser,
    id: int,
) -> list[models.telemetry.Telemetry]:
    async with database.sessions.begin() as session:
        telemetry = await session.scalars(
            select(Telemetry)
            .join(Ship)
            .where(
                and_(
                    Ship.id == id,
                    Ship.owner_id == user.id,
                )
            )
        )

        return [models.telemetry.Telemetry.from_orm(t) for t in telemetry]


@router.post("/add")
async def add_ship(
    user: dependencies.HeaderUser,
    ship_model: models.ship.AddShip,
) -> models.ship.Ship:
    async with database.sessions.begin() as session:
        if (
            await session.scalar(select(Ship).where(Ship.imai == ship_model.imai))
            is not None
        ):
            raise HTTPException(409, "Ship with this imai already exist")

        ship = Ship(
            owner_id=user.id,
            imai=ship_model.imai,
            name=ship_model.name,
            color=ship_model.color,
        )

        session.add(ship)
        await session.flush()
        await session.refresh(ship)

        return models.ship.Ship.from_orm(ship)


@router.put("/update/course")
async def update_course(
    user: dependencies.HeaderUser,
    id: int,
    course: list[tuple[float, float]] | None = None,
) -> models.ship.Ship:
    async with database.sessions.begin() as session:
        ship = await session.scalar(
            select(Ship).where(
                and_(
                    Ship.id == id,
                    Ship.owner_id == user.id,
                )
            )
        )

        if ship is None:
            raise HTTPException(404, "Ship is not found")

        ship.course = course
        await session.flush()
        await session.execute(delete(Telemetry).where(Telemetry.ship_id == id))

        if ship.id in course_pool:
            await course_pool[ship.id].put(course)

        return models.ship.Ship.from_orm(ship)


@router.put("/update")
async def update(
    user: dependencies.HeaderUser,
    id: int,
    ship_model: models.ship.AddShip,
) -> models.ship.Ship:
    async with database.sessions.begin() as session:
        ship = await session.scalar(
            select(Ship).where(
                and_(
                    Ship.id == id,
                    Ship.owner_id == user.id,
                )
            )
        )

        if ship is None:
            raise HTTPException(404, "Ship not found")

        ship.imai = ship_model.imai
        ship.name = ship_model.name
        ship.color = ship_model.color

        await session.flush()

        return models.ship.Ship.from_orm(ship)


@router.delete("/delete")
async def delete_ship(user: dependencies.HeaderUser, id: int) -> models.ship.Ship:
    async with database.sessions.begin() as session:
        ship = await session.scalar(
            select(Ship).where(
                and_(
                    Ship.id == id,
                    Ship.owner_id == user.id,
                )
            )
        )

        if ship is None:
            raise HTTPException(404, "Ship not found")

        await session.delete(ship)
        return models.ship.Ship.from_orm(ship)


@router.websocket("/listen/course")
async def listen_course(
    websocket: WebSocket,
    user: dependencies.QueryUser,
    id: int,
) -> None:
    await websocket.accept()

    if id in course_pool:
        raise WebSocketException(1003, "This ship already connected")

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

    queue: Queue[list[tuple[float, float]] | None] = Queue()
    course_pool[id] = queue

    try:
        while True:
            course = await queue.get()
            await websocket.send_text(json.dumps(course))
    except WebSocketDisconnect:
        course_pool.pop(id)
        await websocket.close()
