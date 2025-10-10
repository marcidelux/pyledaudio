from pydantic import BaseModel, Field
from typing import Callable, Optional


class State(BaseModel):
    power: Optional[bool] = Field(default=None)
    brightness: Optional[int] = Field(default=None)
    effect: Optional[str] = Field(default=None)
    power_changed: Optional[bool] = Field(default=None)
    no_sound_cntr: Optional[int] = Field(default=None)
    no_sound: Optional[bool] = Field(default=None)
    step_time: Optional[float] = Field(default=None)


class StateManager:
    def __init__(self):
        self._state = State(power=True,
                            brightness=255,
                            effect="Snake",
                            power_changed=False,
                            no_sound_cntr=0,
                            no_sound=False,
                            step_time=30.0)
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

    @property
    def power_changed(self):
        return self._state.power_changed

    @power_changed.setter
    def power_changed(self, val: bool):
        self._state.power_changed = val

    @property
    def no_sound_cntr(self):
        return self._state.no_sound_cntr

    @no_sound_cntr.setter
    def no_sound_cntr(self, val: int):
        self._state.no_sound_cntr = val

    @property
    def no_sound(self):
        return self._state.no_sound

    @no_sound.setter
    def no_sound(self, val: bool):
        self._state.no_sound = val

    @property
    def step_time(self):
        return self._state.step_time

    @step_time.setter
    def step_time(self, val: float):
        self._state.step_time = val

    def __str__(self):
        return f"State(power={self.power}, brightness={self.brightness}, effect={self.effect})"


state_manager = StateManager()
