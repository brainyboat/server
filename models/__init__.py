import pydantic
import json


class BaseModel(pydantic.BaseModel):
    class Config:
        orm_mode = True
        allow_inf_nan = False

    def serializable(self) -> dict:
        return json.loads(self.json())


from . import user
from . import ship
from . import telemetry
