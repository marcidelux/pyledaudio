from .static import EffectStatic
from .dynamic import EffectDynamic, spectrumEffect
from typing import List


class EffectsManager:
    def __init__(self):
        self.dynamic_effects: List[EffectDynamic] = [
            spectrumEffect]
        self.static_effects: List[EffectStatic] = []
        self.effects_map = {
            "dynamic": self.dynamic_effects,
            "static": self.static_effects
        }
        self.mode = "dynamic"  # Default mode is dynamic
        self.active_effects = self.effects_map[self.mode]
        self.dynamic_index = 0
        self.static_index = 0

    def current(self) -> Effect:
        return self.effects[self.current_index]

    def next_effect(self) -> Effect:
        self.current_index = (self.current_index + 1) % len(self.effects)
        return self.current()


effect_manager = EffectsManager()
