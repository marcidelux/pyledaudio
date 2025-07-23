from .static.bottom_triangles import bottom_triangles
from .static.side_triangles import side_triangles
from .static.body_triangles import body_triangles
from .static.snake import snake

from .dynamic.spectrum_octagon import spectrum_octagon
from .dynamic.spectrum_triangles import spectrum_triangles
from .dynamic.spectrum_two_lines import spectrum_two_lines
from .dynamic.beat_blast import beat_blast
from .dynamic.beat_octagon import beat_octagon

from .utils import Effect

from .memory_manager import MemoryManager, EffectList, EffectPair
from typing import Optional, List, Dict, Callable
from http import HTTPStatus


class EffectManager:
    def __init__(self, effects_map: dict[str, Effect], dynamic_names: list[str], static_names: list[str]):
        self._effects_map = effects_map

        self.on_change_callback: Optional[Callable[[None], None]] = None
        self.current_effects_list: EffectList = None
        self.current_pair: EffectPair = None
        self.current_list_index: int = 0
        self.memory_manager = MemoryManager()

        self.current_primary_effect: Effect = None
        self.current_secondary_effect: Effect = None

        # load the static and dynamic effect lists
        self.memory_manager.add_effect_list("static", switch_interval=30)
        self.memory_manager.add_effect_list("dynamic", switch_interval=30)
        self.memory_manager.add_effects_to_list(
            "static", [EffectPair(primary=name, secondary=None) for name in static_names])
        self.memory_manager.add_effects_to_list(
            "dynamic", [EffectPair(primary=name, secondary=None) for name in dynamic_names])

        self.select_effects_list("dynamic")
        self._select_effect_pair_by_index(self.current_list_index)

    def set_on_change_callback(self, callback: Callable[[None], None]) -> None:
        self.on_change_callback = callback

    def select_effects_list(self, list_name: str) -> int:
        el = self.memory_manager.get_effect_list(list_name)
        if el is None:
            return HTTPStatus.NOT_FOUND
        self.current_effects_list = el
        self.current_list_index = 0
        self._select_effect_pair_by_index(0)
        return HTTPStatus.OK

    def _select_effect_pair_by_index(self, index: int) -> int:
        if self.current_effects_list is None:
            return HTTPStatus.NOT_FOUND
        if index < 0 or index >= len(self.current_effects_list.effects):
            return HTTPStatus.BAD_REQUEST
        self.current_list_index = index
        self.current_pair = self.current_effects_list.effects[index]
        self._set_effects_by_pair()
        return HTTPStatus.OK

    def _set_effects_by_pair(self) -> None:
        if self.current_pair is None:
            return
        self.current_primary_effect = self._effects_map.get(
            self.current_pair.primary)
        self.current_secondary_effect = self._effects_map.get(
            self.current_pair.secondary)
        if self.on_change_callback:
            self.on_change_callback()

    def set_primary_effect_by_name(self, name: str) -> int:
        if name not in self._effects_map:
            return HTTPStatus.NOT_FOUND
        self.current_pair.primary = name
        self.current_primary_effect = self._effects_map[name]
        if self.on_change_callback:
            self.on_change_callback()
        return HTTPStatus.OK

    def set_secondary_effect_by_name(self, name: Optional[str]) -> int:
        if name == "None":
            print("Setting secondary effect to None")
            self.current_pair.secondary = None
            self.current_secondary_effect = None
            if self.on_change_callback:
                self.on_change_callback()
            return HTTPStatus.OK

        if name is not None and name not in self._effects_map:
            return HTTPStatus.NOT_FOUND

        self.current_pair.secondary = name
        self.current_secondary_effect = self._effects_map.get(name)
        if self.on_change_callback:
            self.on_change_callback()

        return HTTPStatus.OK

    def next_effect_pair(self) -> int:
        if self.current_effects_list is None:
            return HTTPStatus.NOT_FOUND

        if self.current_list_index + 1 >= len(self.current_effects_list.effects):
            self.current_list_index = 0
        else:
            self.current_list_index += 1

        if self._select_effect_pair_by_index(self.current_list_index) != HTTPStatus.OK:
            return HTTPStatus.NOT_FOUND

        return self.current_list_index

    def previous_effect_pair(self) -> int:
        if self.current_effects_list is None:
            return HTTPStatus.NOT_FOUND

        if self.current_list_index - 1 < 0:
            self.current_list_index = len(
                self.current_effects_list.effects) - 1
        else:
            self.current_list_index -= 1

        if self._select_effect_pair_by_index(self.current_list_index) != HTTPStatus.OK:
            return HTTPStatus.NOT_FOUND

        return self.current_list_index


all_effects_map = {
    spectrum_octagon.config.name: spectrum_octagon,
    spectrum_triangles.config.name: spectrum_triangles,
    bottom_triangles.config.name: bottom_triangles,
    side_triangles.config.name: side_triangles,
    body_triangles.config.name: body_triangles,
    beat_blast.config.name: beat_blast,
    beat_octagon.config.name: beat_octagon,
    spectrum_two_lines.config.name: spectrum_two_lines,
    snake.config.name: snake
}

dynamic_names = [
    spectrum_octagon.config.name,
    spectrum_triangles.config.name,
    beat_blast.config.name,
    beat_octagon.config.name,
    spectrum_two_lines.config.name]
static_names = [
    bottom_triangles.config.name,
    side_triangles.config.name,
    body_triangles.config.name,
    snake.config.name]

effect_manager = EffectManager(
    effects_map=all_effects_map,
    dynamic_names=dynamic_names,
    static_names=static_names
)
