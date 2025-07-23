# Third party imports
from fastapi import FastAPI
from http import HTTPStatus

# Project level imports
from effects.effects_manager import effect_manager, static_names, dynamic_names, EffectPair
from state import state_manager

# Local imports
from .models import (
    PowerRequest,
    BrightnessRequest,
    EffectPreviewRequest,
    SelectEffectsListRequest,
    AddEffectPairToCurrentListRequest
)
from . import config


def register_endpoints(app: FastAPI):
    @app.get("/health")
    def hello():
        return {200: "OK"}

    @app.get("/config")
    def get_config():
        FULL_COLOR_PALETTE = [
            '#FF0000', '#00FF00', '#0000BB', '#00FF00', '#00FFFF', '#0000FF', '#8B00FF',
            '#FF1493', '#DC143C', '#FFA500', '#FFD700', '#ADFF2F', '#32CD32', '#008080',
            '#4682B4', '#1E90FF', '#4169E1', '#4B0082', '#9400D3', '#FF69B4', '#CD5C5C',
            '#FF4500', '#FF6347', '#FF8C00', '#20B2AA', '#40E0D0', '#7FFF00', '#7CFC00',
            '#00FA9A', '#00CED1'
        ]
        num_bands = config.N_FFT_BINS
        # Select only as many colors as needed
        colors = FULL_COLOR_PALETTE[:num_bands]
        return {
            "num_bands": num_bands,
            "colors": colors
        }

    @app.post("/power")
    def set_power(req: PowerRequest):
        if req.power is not None:
            state_manager.power = req.power
            print(state_manager)
        else:
            print("No power value provided in request.")

        return {"power": state_manager.power}

    @app.post("/brightness")
    def set_brightness(req: BrightnessRequest):
        if req.brightness is not None:
            state_manager.brightness = req.brightness
            print(state_manager)
        else:
            print("No brightness value provided in request.")

        return {"brightness": state_manager.brightness}

    @app.post("/effect-preview")
    def set_effect_preview(req: EffectPreviewRequest):
        if req.effect is not None and req.primary is not None:
            if req.primary:
                effect_manager.set_primary_effect_by_name(req.effect)
            else:
                effect_manager.set_secondary_effect_by_name(req.effect)
            print(f"Preview effect set to: {req.effect}")
        else:
            print("No effect value provided in request.")

        return {"effect": req.effect}

    @app.get("/effects-lists-names")
    def get_effects_lists_names():
        effects_lists_names = effect_manager.memory_manager.get_names()
        print(f"Available effects lists: {effects_lists_names}")
        if effects_lists_names is None:
            return {"error": "No effects lists found"}, 404
        return {"effects_lists_names": effects_lists_names}

    @app.post("/select-effects-list")
    def post_select_effects_list(req: SelectEffectsListRequest):
        if req.name is None:
            return {"error": "Effects list name is required"}, 400

        effects_list = effect_manager.memory_manager.get_effect_list(req.name)
        if effects_list is None:
            return {"error": f"Effects list '{req.name}' not found"}, HTTPStatus.NOT_FOUND

        if effect_manager.select_effects_list(req.name) == HTTPStatus.NOT_FOUND:
            return {"error": f"Effects list '{req.name}' not found"}, HTTPStatus.NOT_FOUND

        return {"effects_list": effects_list}

    @app.post("/next-effect-pair")
    def post_next_effect_pair():
        next_index = effect_manager.next_effect_pair()
        if next_index == HTTPStatus.NOT_FOUND:
            return {"error": "Current effects list not selected"}, HTTPStatus.NOT_FOUND

        return {"current_index": next_index}

    @app.post("/previous-effect-pair")
    def post_previous_effect_pair():
        previous_index = effect_manager.previous_effect_pair()
        if previous_index == HTTPStatus.NOT_FOUND:
            return {"error": "Current effects list not selected"}, HTTPStatus.NOT_FOUND

        return {"current_index": previous_index}

    @app.post("/add-effect-pair-to-current-list")
    def post_add_effect_pair_to_current_list(req: AddEffectPairToCurrentListRequest):
        if req.primary is None or req.primary == "":
            return {"error": "Primary effect name is required"}, HTTPStatus.BAD_REQUEST

        if effect_manager.memory_manager.add_effect_to_list(
                effect_manager.current_effects_list.name,
                EffectPair(primary=req.primary, secondary=req.secondary)) == HTTPStatus.NOT_FOUND:
            return {"error": f"Current effects list '{effect_manager.current_effects_list.name}' not found"}, HTTPStatus.NOT_FOUND

        effects_list = effect_manager.memory_manager.get_effect_list(
            effect_manager.current_effects_list.name)

        return {"effects_list": effects_list}

    @app.get("/effects-static")
    def get_static_effects():
        return {"effects": static_names}

    @app.get("/effects-dynamic")
    def get_dynamic_effects():
        return {"effects": dynamic_names}
