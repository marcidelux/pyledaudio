let effectList;
let currentEffectsList;
let primaryEffect;
let secondaryEffect;
let prevEffectBt;
let nextEffectBt;

document.addEventListener("DOMContentLoaded", () => {
    createToggleSwitch("#power-sw", true, "POWER", (state) => {
        postPower(state);
    });

    createSlider("#brightness-sb", 10, 255, 255, "brightness", (val) => {
        postBrightness(val);
    });

    primaryEffect = createDropdown("#primary-effect", "Eff 1", [], (effectName) => {
        postEffect(effectName, true);
    });

    secondaryEffect = createDropdown("#secondary-effect", "Eff 2", [], (effectName) => {
        postEffect(effectName, false);
    });

    createButton("#add-effect-bt", "Add Effect to List", () => {
        addEffectToSelectedList();
    });

    currentEffectsList = createDropdown("#current-effects-list", "Current Effects", [], (effectName) => {
        currentEffectsListSelected(effectName);
    });

    prevEffectBt = createButton("#prev-effect-bt", "Prev Effect", () => {
        prevEffectClicked();
    });

    nextEffectBt = createButton("#next-effect-bt", "Next Effect", () => {
        nextEffectClicked();
    });

    effectList = createEffectsListView("#effects-list-view", "Effects List", []);

    fetch("/effects-lists-names")
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! Status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            const list = data.effects_lists_names;
            if (Array.isArray(list)) {
                const items = list.map(name => ({
                    label: name,
                    value: name
                }));
                currentEffectsList.setItems(list);
                currentEffectsListSelected(list[0]);
            } else {
                console.warn("Unexpected response format:", data);
            }
        })
        .catch(err => {
            console.error("Failed to fetch effects lists names:", err);
        });


    Promise.all([
        fetch("/effects-static").then(res => res.json()),
        fetch("/effects-dynamic").then(res => res.json())
    ])
        .then(([staticData, dynamicData]) => {
            const combinedItems = [];

            if (Array.isArray(staticData.effects)) {
                staticData.effects.forEach(name => {
                    combinedItems.push({
                        label: `static - ${name}`,
                        value: name
                    });
                });
            }

            if (Array.isArray(dynamicData.effects)) {
                dynamicData.effects.forEach(name => {
                    combinedItems.push({
                        label: `dynamic - ${name}`,
                        value: name
                    });
                });
            }

            primaryEffect.setItems(combinedItems);

            combinedItems.unshift({
                label: "None",
                value: "None"
            });

            secondaryEffect.setItems(combinedItems);
        })
        .catch(err => {
            console.error("Failed to fetch effects:", err);
        });

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

function postEffect(effectName, isPrimary) {
    fetch("/effect-preview", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ effect: effectName, primary: isPrimary })
    })
        .then(res => res.json())
        .then(data => console.log(`effect response:`, data))
        .catch(err => console.error(`Error sending effect:`, err));
}

function currentEffectsListSelected(effectsListName) {
    fetch("/select-effects-list", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name: effectsListName })
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to fetch effects list '${effectsListName}'. Status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            if (data.effects_list && Array.isArray(data.effects_list.effects)) {
                effectList.load(data.effects_list);
                effectList.setActive(0);
            } else {
                console.warn("Unexpected effect list format:", data);
            }
        })
        .catch(err => {
            console.error("Error loading selected effects list:", err);
        });
}

function addEffectToSelectedList() {
    const primaryEffectValue = primaryEffect.getValue();
    const secondaryEffectValue = secondaryEffect.getValue();

    if (!primaryEffectValue || primaryEffectValue === "None") {
        console.warn("Primary effect is required.");
        return;
    }

    fetch("/add-effect-pair-to-current-list", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            primary: primaryEffectValue,
            secondary: secondaryEffectValue === "None" ? null : secondaryEffectValue
        })
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to add effect pair. Status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            if (data.effects_list && Array.isArray(data.effects_list.effects)) {
                effectList.load(data.effects_list);
            } else {
                console.warn("Unexpected response format:", data);
            }
        })
        .catch(err => {
            console.error("Error adding effect pair to current list:", err);
        });
}

function nextEffectClicked() {
    fetch("/next-effect-pair", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to fetch next effect. Status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            console.log("Next effect response:", data);
            effectList.setActive(data.current_index);
        })
        .catch(err => {
            console.error("Error fetching next effect:", err);
        });
}

function prevEffectClicked() {
    fetch("/previous-effect-pair", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to fetch previous effect. Status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            console.log("Previous effect response:", data);
            effectList.setActive(data.current_index);
        })
        .catch(err => {
            console.error("Error fetching previous effect:", err);
        });
}