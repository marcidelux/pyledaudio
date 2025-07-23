from pydantic import BaseModel
from typing import Optional


class PowerRequest(BaseModel):
    power: Optional[bool] = None


class BrightnessRequest(BaseModel):
    brightness: Optional[int] = None


class EffectPreviewRequest(BaseModel):
    effect: Optional[str] = None
    primary: Optional[bool] = None


class SelectEffectsListRequest(BaseModel):
    name: str


class AddEffectPairToCurrentListRequest(BaseModel):
    primary: str
    secondary: Optional[str] = None
