from .static.traveling_dots import travelingDots
from .static.triangle_lines import triangleLines
from .static.bottom_triangles import bottom_triangles
from .static.side_triangles import side_triangles
from .static.body_triangles import body_triangles
from .dynamic.spectrum import spectrum4
from .dynamic.spectrum_octagon import spectrum_octagon
from .dynamic.spectrum_triangles import spectrum_triangles
from .utils import Effect


class EffectManager:
    def __init__(self, all_effects: dict[str, Effect], dynamic_names: list[str], static_names: list[str]):
        self.all_effects = all_effects
        self.effect_lists: dict[str, list[str]] = {
            "dynamic": dynamic_names,
            "static": static_names
        }
        self.active_list_name: str = "dynamic"
        self.current_index: int = 0

    def get_effect_by_name(self, name: str) -> Effect:
        if name not in self.all_effects:
            raise ValueError(f"No such effect: {name}")
        return self.all_effects[name]

    def get_current(self) -> Effect:
        current_list = self.effect_lists[self.active_list_name]
        current_name = current_list[self.current_index]
        return self.all_effects[current_name]

    def get_current_name(self) -> str:
        return self.effect_lists[self.active_list_name][self.current_index]

    def set_current(self, name: str):
        names = self.effect_lists[self.active_list_name]
        if name in names:
            self.current_index = names.index(name)

    def next(self):
        names = self.effect_lists[self.active_list_name]
        self.current_index = (self.current_index + 1) % len(names)

    def switch_list(self, list_name: str):
        if list_name not in self.effect_lists:
            raise ValueError(f"No such effect list: {list_name}")
        self.active_list_name = list_name
        self.current_index = 0

    def add_list(self, name: str, effect_names: list[str]):
        if name in ["dynamic", "static"]:
            raise ValueError("Cannot overwrite built-in lists.")
        valid_names = [n for n in effect_names if n in self.all_effects]
        self.effect_lists[name] = valid_names

    def delete_list(self, name: str):
        if name in ["dynamic", "static"]:
            raise ValueError("Cannot delete built-in lists.")
        self.effect_lists.pop(name, None)

    def list_names(self) -> list[str]:
        return list(self.effect_lists.keys())

    def get_list_elements(self, list_name: str) -> list[str]:
        if list_name not in self.effect_lists:
            raise ValueError(f"No such effect list: {list_name}")
        return self.effect_lists[list_name]


all_effects = {
    travelingDots.config.name: travelingDots,
    triangleLines.config.name: triangleLines,
    spectrum4.config.name: spectrum4,
    spectrum_octagon.config.name: spectrum_octagon,
    spectrum_triangles.config.name: spectrum_triangles,
    bottom_triangles.config.name: bottom_triangles,
    side_triangles.config.name: side_triangles,
    body_triangles.config.name: body_triangles
}

dynamic_names = [spectrum4.config.name,
                 spectrum_octagon.config.name,
                 spectrum_triangles.config.name]
static_names = [travelingDots.config.name,
                triangleLines.config.name,
                bottom_triangles.config.name,
                side_triangles.config.name,
                body_triangles.config.name]

effect_manager = EffectManager(
    all_effects=all_effects,
    dynamic_names=dynamic_names,
    static_names=static_names
)
