from .spectrums import spectrumEffect
from .static import triangleEffect
from .test import testEffects
from typing import List
from .effect import Effect

class EffectsManager:
    def __init__(self):
        self.effects: List[Effect] = [spectrumEffect, triangleEffect, testEffects]
        self.current_index = 0

    def current(self) -> Effect:
        return self.effects[self.current_index]

    def next_effect(self) -> Effect:
        self.current_index = (self.current_index + 1) % len(self.effects)
        return self.current()

effect_manager = EffectsManager()