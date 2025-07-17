from pydantic import BaseModel, Field
from typing import Callable, Optional


class State(BaseModel):
    power: Optional[bool] = Field(default=None)
    brightness: Optional[int] = Field(default=None)
    effect: Optional[str] = Field(default=None)


class StateManager:
    def __init__(self):
        self._state = State(power=True,
                            brightness=255,
                            effect="Snake")
        self._on_effect_change: Optional[Callable[[str], None]] = None

    def set_effect_callback(self, callback: Callable[[str], None]):
        self._on_effect_change = callback

    @property
    def effect(self):
        return self._state.effect

    @effect.setter
    def effect(self, value: str):
        if value != self._state.effect:
            self._state.effect = value
            if self._on_effect_change:
                self._on_effect_change(value)

    # Add similar wrappers if needed
    @property
    def brightness(self):
        return self._state.brightness

    @brightness.setter
    def brightness(self, val: int):
        self._state.brightness = val

    @property
    def power(self):
        return self._state.power

    @power.setter
    def power(self, val: bool):
        self._state.power = val

    def __str__(self):
        return f"State(power={self.power}, brightness={self.brightness}, effect={self.effect})"


state_manager = StateManager()
