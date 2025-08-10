from fastapi import FastAPI
from fastapi.responses import JSONResponse
from http import HTTPStatus

from effects.effects_manager import effect_manager, EffectPair, EffectList
from state import state_manager

from .models import (
    PowerRequest,
    BrightnessRequest,
    AddEffectListRequest,
    SelectCurrentEffectByIndexRequest
)
from . import config


def register_endpoints(app: FastAPI):
    @app.get("/health")
    def hello():
        return JSONResponse(content={200: "OK"}, status_code=HTTPStatus.OK)

    @app.get("/config")
    def get_config():
        FULL_COLOR_PALETTE = [
            '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43',
            '#ffa600', '#DC143C', '#FFA500', '#FFD700', '#ADFF2F', '#32CD32', '#008080',
            '#4682B4', '#1E90FF', '#4169E1', '#4B0082', '#9400D3', '#FF69B4', '#CD5C5C',
            '#FF4500', '#FF6347', '#FF8C00', '#20B2AA', '#40E0D0', '#7FFF00', '#7CFC00',
            '#00FA9A', '#00CED1'
        ]
        num_bands = config.N_FFT_BINS
        colors = FULL_COLOR_PALETTE[:num_bands]
        return {"num_bands": num_bands, "colors": colors}

    @app.get("/state")
    def get_state():
        return JSONResponse(content={
            "power": state_manager.power,
            "brightness": state_manager.brightness
        }, status_code=HTTPStatus.OK)

    @app.post("/state/power")
    def set_power(req: PowerRequest):
        if req.power is None:
            return JSONResponse(content={"error": "No power value provided"}, status_code=HTTPStatus.BAD_REQUEST)
        if state_manager.power == req.power:
            return JSONResponse(content={"info": "Power state unchanged"}, status_code=HTTPStatus.OK)

        state_manager.power_changed = True
        state_manager.power = req.power

        return JSONResponse(content={"power": state_manager.power}, status_code=HTTPStatus.OK)

    @app.post("/state/brightness")
    def set_brightness(req: BrightnessRequest):
        if req.brightness is None:
            return JSONResponse(content={"error": "No brightness value provided"}, status_code=HTTPStatus.BAD_REQUEST)
        state_manager.brightness = req.brightness
        return JSONResponse(content={"brightness": state_manager.brightness}, status_code=HTTPStatus.OK)

    @app.get("/effect-list")
    def get_effect_lists():
        return JSONResponse(content=[el.model_dump() for el in effect_manager.list_manager.lists],
                            status_code=HTTPStatus.OK)

    @app.get("/effect-list/{list_name}")
    def get_effect_list_by_name(list_name: str):
        effect_list = effect_manager.list_manager.get_list(list_name)
        if effect_list is None:
            return JSONResponse(content={"error": "Effect list not found"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(content=effect_list.model_dump(), status_code=HTTPStatus.OK)

    @app.get("/effect-list-names")
    def get_effect_list_names():
        return JSONResponse(content={"list_names": effect_manager.list_manager.get_list_names()},
                            status_code=HTTPStatus.OK)

    @app.get("/effect-list-current")
    def get_current_effect_list():
        if effect_manager.current_list is None:
            return JSONResponse(content={"error": "No current effect list"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(content=effect_manager.current_list.model_dump(), status_code=HTTPStatus.OK)

    @app.get("/effect-list-current/name")
    def get_current_effect_list_name():
        if effect_manager.current_list is None:
            return JSONResponse(content={"error": "No current effect list"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(content={"name": effect_manager.current_list.name}, status_code=HTTPStatus.OK)

    @app.get("/effect-list-current/pair")
    def get_current_effect_pair():
        if effect_manager.current_pair is None:
            return JSONResponse(content={"error": "No current effect pair"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(content=effect_manager.current_pair.model_dump(), status_code=HTTPStatus.OK)

    @app.get("/effect-list-current/index")
    def get_current_effect_index():
        return JSONResponse(content={"index": effect_manager.current_index}, status_code=HTTPStatus.OK)

    @app.post("/effect-list-current/index")
    def set_current_effect_index(req: SelectCurrentEffectByIndexRequest):
        if effect_manager.current_list is None:
            return JSONResponse(content={"error": "No current effect list"}, status_code=HTTPStatus.NOT_FOUND)

        if len(effect_manager.current_list.effects) == 0:
            return JSONResponse(content={"info": "Current effect list is empty"}, status_code=HTTPStatus.OK)

        if req.index < 0 or req.index >= len(effect_manager.current_list.effects):
            return JSONResponse(content={"error": "Index out of bounds"}, status_code=HTTPStatus.BAD_REQUEST)

        effect_manager.select_effect_pair_by_index(req.index)
        return JSONResponse(content={"index": effect_manager.current_index}, status_code=HTTPStatus.OK)

    @app.post("/effect-list-current/next")
    def select_next_effect():
        if effect_manager.current_list is None:
            return JSONResponse(content={"error": "No current effect list"}, status_code=HTTPStatus.NOT_FOUND)
        new_index = effect_manager.next_effect_pair()
        if new_index == HTTPStatus.NOT_FOUND:
            return JSONResponse(content={"error": "No next effect pair found"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(content={"index": new_index}, status_code=HTTPStatus.OK)

    @app.post("/effect-list-current/previous")
    def select_previous_effect():
        if effect_manager.current_list is None:
            return JSONResponse(content={"error": "No current effect list"}, status_code=HTTPStatus.NOT_FOUND)
        new_index = effect_manager.previous_effect_pair()
        if new_index == HTTPStatus.NOT_FOUND:
            return JSONResponse(content={"error": "No previous effect pair found"}, status_code=HTTPStatus.NOT_FOUND)
        return JSONResponse(content={"index": new_index}, status_code=HTTPStatus.OK)

    @app.post("/effect-list")
    def post_effect_list(req: AddEffectListRequest):
        if not req.name:
            return JSONResponse(content={"error": "Effects list name is required"}, status_code=HTTPStatus.BAD_REQUEST)

        new_list = EffectList(
            name=req.name, switch_interval=req.switch_interval or 30, effects=req.effects or [])

        if effect_manager.list_manager.add_list(new_list) == HTTPStatus.CONFLICT:
            return JSONResponse(content={"error": f"Effects list '{req.name}' already exists"},
                                status_code=HTTPStatus.CONFLICT)

        effect_manager.select_list(req.name)
        return get_effect_lists()

    @app.post("/effect-pair/preview")
    def set_effect_preview(req: EffectPair):
        if req.primary is not None:
            effect_manager.set_primary_effect_by_name(req.primary)
            print(f"Primary effect set to: {req.primary}")
        if req.secondary is not None:
            effect_manager.set_secondary_effect_by_name(req.secondary)
            print(f"Secondary effect set to: {req.secondary}")
        else:
            effect_manager.set_secondary_effect_by_name(None)
            print("Secondary effect cleared")

        return JSONResponse(content={"status": "Preview updated"}, status_code=HTTPStatus.OK)

    @app.post("/effect-list/{list_name}")
    def select_effect_list(list_name: str):
        if not list_name:
            return JSONResponse(content={"error": "Effects list name is required"}, status_code=HTTPStatus.BAD_REQUEST)
        if effect_manager.select_list(list_name) == HTTPStatus.NOT_FOUND:
            return JSONResponse(content={"error": f"Effects list '{list_name}' not found"},
                                status_code=HTTPStatus.NOT_FOUND)
        return get_effect_list_by_name(list_name)

    @app.delete("/effect-list/{list_name}")
    def remove_effect_list(list_name: str):
        if not list_name:
            return JSONResponse(content={"error": "Effects list name is required"}, status_code=HTTPStatus.BAD_REQUEST)
        if list_name in ("static", "dynamic"):
            return JSONResponse(content={"error": "Cannot remove static or dynamic lists"},
                                status_code=HTTPStatus.FORBIDDEN)

        status = effect_manager.list_manager.remove_list(list_name)
        if status == HTTPStatus.NOT_FOUND:
            return JSONResponse(content={"error": f"Effect list '{list_name}' not found"},
                                status_code=HTTPStatus.NOT_FOUND)

        if effect_manager.current_list and effect_manager.current_list.name == list_name:
            effect_manager.select_list(
                effect_manager.list_manager.get_list_names()[0])

        return get_effect_lists()

    @app.post("/effect-list/{list_name}/append")
    def append_effect_pair_to_list(list_name: str, new_effect: EffectPair):
        if not list_name:
            return JSONResponse(content={"error": "Effects list name is required"}, status_code=HTTPStatus.BAD_REQUEST)
        if not new_effect.primary:
            return JSONResponse(content={"error": "Primary effect is required"}, status_code=HTTPStatus.BAD_REQUEST)
        if list_name in ("static", "dynamic"):
            return JSONResponse(content={"error": "Cannot append to static or dynamic lists"},
                                status_code=HTTPStatus.FORBIDDEN)

        status = effect_manager.list_manager.add_effect_to_list(
            list_name, new_effect)
        if status == HTTPStatus.NOT_FOUND:
            return JSONResponse(content={"error": f"Effect list '{list_name}' not found"},
                                status_code=HTTPStatus.NOT_FOUND)
        if status == HTTPStatus.CONFLICT:
            return JSONResponse(content={"error": f"Effect pair {new_effect} already exists in list '{list_name}'"},
                                status_code=HTTPStatus.CONFLICT)

        return get_effect_list_by_name(list_name)

    @app.delete("/effect-list/{list_name}/remove")
    def remove_effect_pair_from_list(list_name: str, effect_to_remove: EffectPair):
        if not list_name or not effect_to_remove.primary:
            return JSONResponse(content={"error": "Primary effect is required"}, status_code=HTTPStatus.BAD_REQUEST)
        if list_name in ("static", "dynamic"):
            return JSONResponse(content={"error": "Cannot remove from static or dynamic lists"},
                                status_code=HTTPStatus.FORBIDDEN)

        status = effect_manager.list_manager.remove_effect_from_list(
            list_name, effect_to_remove)
        if status == HTTPStatus.NOT_FOUND:
            return JSONResponse(content={"error": f"Effect list '{list_name}' not found"},
                                status_code=HTTPStatus.NOT_FOUND)
        if status == HTTPStatus.NO_CONTENT:
            return JSONResponse(content={"error": f"Effect pair {effect_to_remove} not found in list '{list_name}'"},
                                status_code=HTTPStatus.NOT_FOUND)

        return get_effect_list_by_name(list_name)
