from typing import Optional, Callable
from http import HTTPStatus

from .utils import Effect

# Effect imports
from .static.bottom_triangles import BottomTriangles
from .static.side_triangles import SideTriangles
from .static.body_triangles import BodyTriangles
from .static.snake import Snake

from .dynamic.spectrum_octagon import SpectrumOctagon
from .dynamic.spectrum_triangles import SpectrumTriangles
from .dynamic.spectrum_two_lines import SpectrumTwoLines
from .dynamic.beat_blast import BeatBlast
from .dynamic.beat_octagon import BeatOctagon
from .dynamic.vu_two_lines import VuTwoLines
from .dynamic.vu_two_lines_top import VuTwoLinesTop

from .list_manager import EffectPair, EffectList, ListsManager


class EffectManager:
    # Dynamic effects
    beat_blast: BeatBlast = BeatBlast()
    beat_octagon: BeatOctagon = BeatOctagon()
    spectrum_octagon: SpectrumOctagon = SpectrumOctagon()
    spectrum_triangles: SpectrumTriangles = SpectrumTriangles()
    spectrum_two_lines: SpectrumTwoLines = SpectrumTwoLines()
    vu_two_lines: VuTwoLines = VuTwoLines()
    vu_two_lines_top: VuTwoLinesTop = VuTwoLinesTop()

    # Static effects
    bottom_triangles: BottomTriangles = BottomTriangles()
    side_triangles: SideTriangles = SideTriangles()
    body_triangles: BodyTriangles = BodyTriangles()
    snake: Snake = Snake()

    all_effects_map: dict[str, Effect] = {
        spectrum_octagon.config.name: spectrum_octagon,
        spectrum_triangles.config.name: spectrum_triangles,
        bottom_triangles.config.name: bottom_triangles,
        side_triangles.config.name: side_triangles,
        body_triangles.config.name: body_triangles,
        beat_blast.config.name: beat_blast,
        beat_octagon.config.name: beat_octagon,
        spectrum_two_lines.config.name: spectrum_two_lines,
        snake.config.name: snake,
        vu_two_lines.config.name: vu_two_lines,
        vu_two_lines_top.config.name: vu_two_lines_top
    }

    dynamic_names: list[str] = [
        spectrum_octagon.config.name,
        spectrum_triangles.config.name,
        beat_blast.config.name,
        beat_octagon.config.name,
        spectrum_two_lines.config.name,
        vu_two_lines.config.name,
        vu_two_lines_top.config.name
    ]

    static_names: list[str] = [
        bottom_triangles.config.name,
        side_triangles.config.name,
        body_triangles.config.name,
        snake.config.name
    ]

    def __init__(self):
        self._effects_map = EffectManager.all_effects_map
        self.dynamic_names = EffectManager.dynamic_names
        self.static_names = EffectManager.static_names

        self.list_manager = ListsManager()

        self.on_change_callback: Optional[Callable[[None], None]] = None
        self.current_list: EffectList = None
        self.current_pair: EffectPair = None
        self.current_index: int = 0

        self.current_primary_effect: Effect = None
        self.current_secondary_effect: Effect = None

        # load the static and dynamic effect lists
        static_effects_lists = EffectList(
            name="static",
            switch_interval=30,
            effects=[EffectPair(primary=name, secondary=None)
                     for name in EffectManager.static_names]
        )
        dynamic_effects_lists = EffectList(
            name="dynamic",
            switch_interval=30,
            effects=[EffectPair(primary=name, secondary=None)
                     for name in EffectManager.dynamic_names]
        )

        self.list_manager.setup(static_effects_lists, dynamic_effects_lists)

        self.select_list("static")

    def set_on_change_callback(self, callback: Callable[[None], None]) -> None:
        self.on_change_callback = callback

    def select_list(self, list_name: str) -> HTTPStatus:
        l = self.list_manager.get_list(list_name)
        if l is None:
            return HTTPStatus.NOT_FOUND

        self.current_list = l
        self.current_index = 0
        self.select_pair(self.current_index)

        print(f"Selected effect list: {self.current_list.name}")

        return HTTPStatus.OK

    def select_pair(self, index: int) -> HTTPStatus:
        if self.current_list is None:
            return HTTPStatus.NOT_FOUND
        if index < 0 or index >= len(self.current_list.effects):
            return HTTPStatus.BAD_REQUEST

        self.current_index = index
        self.current_pair = self.current_list.effects[index]
        self._set_effects_by_pair()

        print(
            f"Selected effect pair: {self.current_pair.primary} and {self.current_pair.secondary}")

        return HTTPStatus.OK

    def _set_effects_by_pair(self) -> None:
        if self.current_pair is None:
            return

        if self.current_primary_effect is not None:
            self.current_primary_effect.clear()
        if self.current_secondary_effect is not None:
            self.current_secondary_effect.clear()

        self.current_primary_effect = self._effects_map.get(
            self.current_pair.primary)
        self.current_secondary_effect = self._effects_map.get(
            self.current_pair.secondary)

        if self.on_change_callback:
            self.on_change_callback()

    def set_primary_effect_by_name(self, name: str) -> int:
        if name not in self._effects_map:
            return HTTPStatus.NOT_FOUND

        if self.current_primary_effect is not None:
            self.current_primary_effect.clear()

        self.current_primary_effect = self._effects_map[name]

        if self.on_change_callback:
            self.on_change_callback()

        return HTTPStatus.OK

    def set_secondary_effect_by_name(self, name: Optional[str]) -> int:
        if self.current_secondary_effect is not None:
            self.current_secondary_effect.clear()

        if name == "None" or name is None:
            self.current_secondary_effect = None
            if self.on_change_callback:
                self.on_change_callback()
            return HTTPStatus.OK

        if name not in self._effects_map:
            return HTTPStatus.NOT_FOUND

        self.current_secondary_effect = self._effects_map.get(name)
        if self.on_change_callback:
            self.on_change_callback()
        return HTTPStatus.OK

    def select_effect_pair_by_index(self, index: int) -> HTTPStatus:
        if self.current_list is None:
            return HTTPStatus.NOT_FOUND

        if index < 0 or index >= len(self.current_list.effects):
            return HTTPStatus.BAD_REQUEST

        self.current_index = index
        return self.select_pair(self.current_index)

    def next_effect_pair(self) -> int:
        if self.current_list is None:
            return HTTPStatus.NOT_FOUND

        if self.current_index + 1 >= len(self.current_list.effects):
            self.current_index = 0
        else:
            self.current_index += 1

        if self.select_pair(self.current_index) != HTTPStatus.OK:
            return HTTPStatus.NOT_FOUND

        return self.current_index

    def previous_effect_pair(self) -> int:
        if self.current_list is None:
            return HTTPStatus.NOT_FOUND

        if self.current_index - 1 < 0:
            self.current_index = len(
                self.current_list.effects) - 1
        else:
            self.current_index -= 1

        if self.select_pair(self.current_index) != HTTPStatus.OK:
            return HTTPStatus.NOT_FOUND

        return self.current_index


effect_manager = EffectManager()
