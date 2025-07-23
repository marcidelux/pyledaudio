from typing import List, Optional
from pydantic import BaseModel
import json
import os
from http import HTTPStatus


class EffectPair(BaseModel):
    primary: str
    secondary: Optional[str] = None


class EffectList(BaseModel):
    name: str
    switch_interval: int
    effects: List[EffectPair]


class MemoryManager:
    def __init__(self, filepath="memory.json"):
        self.filepath = filepath
        self.effect_lists: List[EffectList] = []
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError("Empty file")
                    data = json.loads(content)
                    self.effect_lists = [EffectList(**el) for el in data]
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"[MemoryManager] Warning: Failed to load {self.filepath}: {e}")
                self.effect_lists = []  # fallback to empty
                self._save()
        else:
            self._save()

    def _save(self):
        with open(self.filepath, "w") as f:
            json.dump([el.model_dump()
                      for el in self.effect_lists], f, indent=4)

    def get_names(self):
        return [el.name for el in self.effect_lists]

    def get_effect_list(self, name: str) -> Optional[EffectList]:
        for el in self.effect_lists:
            if el.name == name:
                return el
        print(f"Effect list '{name}' not found.")
        return None

    def add_effect_list(self, name: str, switch_interval: int = 30) -> int:
        if any(el.name == name for el in self.effect_lists):
            print(f"Effect list '{name}' already exists.")
            return HTTPStatus.CONFLICT
        self.effect_lists.append(EffectList(
            name=name, switch_interval=switch_interval, effects=[]))
        self._save()

    def add_effect_to_list(self, list_name: str, effect: EffectPair) -> int:
        for el in self.effect_lists:
            if el.name == list_name:
                if any(ep.primary == effect.primary and ep.secondary == effect.secondary for ep in el.effects):
                    print(
                        f"Effect '{effect.primary}' with secondary '{effect.secondary}' already exists in the list.")
                    return HTTPStatus.CONFLICT
                el.effects.append(effect)
                self._save()
                return HTTPStatus.CREATED
        print(f"Effect list '{list_name}' not found.")
        return HTTPStatus.NOT_FOUND

    def add_effects_to_list(self, list_name: str, effects: List[EffectPair]) -> HTTPStatus:
        for el in self.effect_lists:
            if el.name == list_name:
                new_effects = []
                for effect in effects:
                    is_duplicate = any(
                        e.primary == effect.primary and e.secondary == effect.secondary
                        for e in el.effects
                    )
                    if is_duplicate:
                        print(
                            f"Effect '{effect.primary}' with secondary '{effect.secondary}' already exists.")
                    else:
                        new_effects.append(effect)

                if new_effects:
                    el.effects.extend(new_effects)
                    self._save()
                    return HTTPStatus.CREATED

                return HTTPStatus.OK  # All effects were duplicates

        print(f"Effect list '{list_name}' not found.")
        return HTTPStatus.NOT_FOUND

    def remove_effect_from_list(self, list_name: str, primary: str) -> int:
        for el in self.effect_lists:
            if el.name == list_name:
                el.effects = [ep for ep in el.effects if ep.primary != primary]
                self._save()
                return HTTPStatus.NO_CONTENT
        print(f"Effect list '{list_name}' not found.")
        return HTTPStatus.NOT_FOUND

    def remove_effect_list(self, name: str) -> int:
        if not any(el.name == name for el in self.effect_lists):
            print(f"Effect list '{name}' not found.")
            return HTTPStatus.NOT_FOUND
        self.effect_lists = [el for el in self.effect_lists if el.name != name]
        self._save()
        return HTTPStatus.NO_CONTENT

    def update_effect_list(self, name: str, new_data: dict) -> int:
        for i, el in enumerate(self.effect_lists):
            if el.name == name:
                self.effect_lists[i] = EffectList(**new_data)
                self._save()
                return HTTPStatus.OK
        print(f"Effect list '{name}' not found.")
        return HTTPStatus.NOT_FOUND

    def erase(self):
        self.effect_lists = []
        self._save()

    def active(self):
        return self.effect_lists
