from fastapi import APIRouter

from . import dependencies

from . import user
from . import ship
from . import telemetry

router = APIRouter()
router.include_router(user.router)
router.include_router(ship.router)
router.include_router(telemetry.router)
