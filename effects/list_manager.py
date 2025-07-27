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


def print_effect_lists(effect_lists: List[EffectList]) -> None:
    if not effect_lists:
        print("No effect lists found.")
        return

    for el in effect_lists:
        print(f"Effect List: {el.name}, Switch Interval: {el.switch_interval}")
        for effect in el.effects:
            print(
                f"  - Primary: {effect.primary}, Secondary: {effect.secondary or 'None'}")


class MemoryManager:
    def __init__(self, filepath="memory.json"):
        self.filepath = filepath

    def load(self) -> List[EffectList] | None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError("Empty file")
                    data = json.loads(content)
                    return [EffectList(**el) for el in data]

            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"[MemoryManager] Warning: Failed to load {self.filepath}: {e}")
                raise e
        else:
            open(self.filepath, "w").close()
            print(
                f"[MemoryManager] Warning: File {self.filepath} does not exist, creating a new one.")
            return None

    def save(self, effect_lists: List[EffectList]) -> None:
        with open(self.filepath, "w") as f:
            json.dump([el.model_dump()
                      for el in effect_lists], f, indent=4)


class ListsManager:
    def __init__(self):
        self.lists: List[EffectList] = []
        self.memory_manager = MemoryManager()

    def setup(self, static_effects: EffectList, dynamic_effects: EffectList) -> None:
        try:
            # Load existing lists from memory
            loaded_lists = self.memory_manager.load()

            if loaded_lists is not None:
                self.lists = loaded_lists

            if self.add_list(static_effects) == HTTPStatus.CREATED:
                print(f"Static effects list '{static_effects.name}' added.")
            else:
                self.merge_list(static_effects)
                print(
                    f"Static effects list '{static_effects.name}' already exists, merging.")

            if self.add_list(dynamic_effects) == HTTPStatus.CREATED:
                print(f"Dynamic effects list '{dynamic_effects.name}' added.")
            else:
                self.merge_list(dynamic_effects)
                print(
                    f"Dynamic effects list '{dynamic_effects.name}' already exists, merging.")

        except Exception as e:
            print(f"[ListsManager] Error loading lists: {e}")
            self.lists = []

    def get_lists(self) -> List[EffectList] | None:
        return self.lists

    def get_list_names(self) -> List[str]:
        return [el.name for el in self.lists]

    def get_list(self, name: str) -> Optional[EffectList] | None:
        for el in self.lists:
            if el.name == name:
                return el
        print(f"Effect list '{name}' not found.")
        return None

    def add_list(self, effect_list: EffectList) -> HTTPStatus:
        if any(el.name == effect_list.name for el in self.lists):
            print(f"Effect list '{effect_list.name}' already exists.")
            return HTTPStatus.CONFLICT
        self.lists.append(effect_list)
        self.memory_manager.save(self.lists)
        return HTTPStatus.CREATED

    def add_effect_to_list(self, list_name: str, effect_pair: EffectPair) -> HTTPStatus:
        existing_list = self.get_list(list_name)

        if existing_list is None:
            print(f"Effect list '{list_name}' not found.")
            return HTTPStatus.NOT_FOUND

        if list_name == "static" or list_name == "dynamic":
            print(
                f"Cannot add effects to static or dynamic lists.")
            return HTTPStatus.BAD_REQUEST

        for exiting in existing_list.effects:
            if exiting.primary == effect_pair.primary and exiting.secondary == effect_pair.secondary:
                print(
                    f"EffectPair {effect_pair} already exists in list '{list_name}'.")
                return HTTPStatus.CONFLICT

        existing_list.effects.append(effect_pair)
        self.memory_manager.save(self.lists)

        return HTTPStatus.CREATED

    def merge_list(self, effect_list: EffectList) -> HTTPStatus:
        existing_list = self.get_list(effect_list.name)
        if existing_list is None:
            print(f"Effect list '{effect_list.name}' not found.")
            return HTTPStatus.NOT_FOUND

        added_any = False

        for effect in effect_list.effects:
            status = self.add_effect_to_list(effect_list.name, effect)
            if status == HTTPStatus.CREATED:
                added_any = True

        return HTTPStatus.OK if added_any else HTTPStatus.NO_CONTENT

    def remove_list(self, name: str) -> HTTPStatus:
        for i, el in enumerate(self.lists):
            if el.name == name:
                del self.lists[i]
                self.memory_manager.save(self.lists)
                print(f"Effect list '{name}' removed.")
                return HTTPStatus.OK
        print(f"Effect list '{name}' not found.")
        return HTTPStatus.NOT_FOUND

    def remove_effect_from_list(self, list_name: str, effect_pair: EffectPair) -> HTTPStatus:
        existing_list = self.get_list(list_name)

        if existing_list is None:
            print(f"Effect list '{list_name}' not found.")
            return HTTPStatus.NOT_FOUND

        for i, existing in enumerate(existing_list.effects):
            if existing == effect_pair:
                del existing_list.effects[i]
                self.memory_manager.save(self.lists)
                print(
                    f"EffectPair {effect_pair} removed from list '{list_name}'.")
                return HTTPStatus.OK

        print(
            f"EffectPair {effect_pair} not found in list '{list_name}'.")
        return HTTPStatus.NOT_FOUND
