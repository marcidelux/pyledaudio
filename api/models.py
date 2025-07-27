from pydantic import BaseModel
from typing import Optional
from effects.list_manager import EffectPair


class PowerRequest(BaseModel):
    power: Optional[bool] = None


class BrightnessRequest(BaseModel):
    brightness: Optional[int] = None


class AddEffectListRequest(BaseModel):
    name: str
    switch_interval: Optional[int]
    effects: Optional[EffectPair]


class SelectCurrentEffectByIndexRequest(BaseModel):
    index: int
