document.addEventListener("DOMContentLoaded", () => {
    createToggleSwitch("#power-sw", true, "POWER", (state) => {
        postPower(state);
    });

    createSlider("#brightness-sb", 10, 255, 255, "brightness", (val) => {
        postBrightness(val);
    });

    const staticEffects = createDropdown("#static-effects", "static effects", [], (effect) => {
        postEffect(effect);
    });

    const dynamicEffects = createDropdown("#dynamic-effects", "dynamic effects", [], (effect) => {
        postEffect(effect);
    });

    fetch("/effects-static")
        .then(res => res.json())
        .then(data => {
            if (data.effects && Array.isArray(data.effects)) {
                staticEffects.setItems(data.effects); // works if setItems supports plain strings
            }
        })
        .catch(err => console.error("Failed to fetch static effects:", err));


    fetch("/effects-dynamic")
        .then(res => res.json())
        .then(data => {
            if (data.effects && Array.isArray(data.effects)) {
                dynamicEffects.setItems(data.effects); // works if setItems supports plain strings
            }
        })
        .catch(err => console.error("Failed to fetch static effects:", err));
});

function postPower(state) {
    fetch("/power", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ power: state })
    })
        .then(res => res.json())
        .then(data => console.log("Power response:", data))
        .catch(err => console.error("Error sending power state:", err));
}

function postBrightness(value) {
    fetch("/brightness", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ brightness: value })
    })
        .then(res => res.json())
        .then(data => console.log("Brightness response:", data))
        .catch(err => console.error("Error sending brightness value:", err));
}

function postEffect(effectName) {
    fetch("/effect", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ effect: effectName })
    })
        .then(res => res.json())
        .then(data => console.log(`effect response:`, data))
        .catch(err => console.error(`Error sending effect:`, err));
}