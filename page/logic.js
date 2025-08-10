import { API } from "./api.js";
import {
    EffectList,
    EffectPair,
    AddEffectListRequest,
    SelectCurrentEffectByIndexRequest,
    PowerRequest,
    BrightnessRequest
} from './models.js';

let effect_lists = [];

let ui_effect_list_names = null;
let ui_current_effects = null;
let ui_primary_effect = null;
let ui_secondary_effects = null;
let ui_new_list_name = null;
let ui_delete_list_bt = null;

document.addEventListener("DOMContentLoaded", () => {
    createToggleSwitch("#power-sw", true, "POWER", (state) => {
        onClickPowerSwitch(state);
    });

    createSlider("#brightness-sb", 10, 255, 255, "brightness", (val) => {
        onChangeBrightness(val);
    });

    ui_new_list_name = createTextInput("#new-effect-list-name", "New List Name", "Enter new list name");
    createButton("#add-effect-list-bt", "Add New List", () => {
        onCLickAddNewList();
    });
    ui_delete_list_bt = createDeleteButton("#delete-effect-list-bt", "Delete", () => {
        onClickedDeleteList();
    });

    ui_primary_effect = createDropdown("#primary-effect", "Eff 1", [], () => {
        onSelectPreviewEffect();
    });

    ui_secondary_effects = createDropdown("#secondary-effect", "Eff 2", [], () => {
        onSelectPreviewEffect();
    });

    createButton("#add-effect-bt", "Add Effect to List", () => {
        onClickAddEffectToSelectedList();
    });

    ui_effect_list_names = createDropdown("#current-effects-list", "Current List", [], (effectName) => {
        onSelectCurrentEffectListName(effectName);
    });

    createButton("#prev-effect-bt", "Prev Effect", () => {
        onClickedPreviousEffect();
    });

    createButton("#next-effect-bt", "Next Effect", () => {
        onClickedNextEffect();
    });

    ui_current_effects = createEffectsListView("#effects-list-view", (name, primary, secondary) => {
        onCLickedDeleteEffect(name, primary, secondary);
    });

    uiInit();
});

async function onClickPowerSwitch(state) {
    const request = new PowerRequest(state);
    try {
        await API.setPower(request);
        console.log(`Power state set to: ${state}`);
    } catch (err) {
        console.error("Error setting power state:", err);
    }
}

async function onChangeBrightness(value) {
    const request = new BrightnessRequest(value);
    try {
        await API.setBrightness(request);
        console.log(`Brightness set to: ${value}`);
    } catch (err) {
        console.error("Error setting brightness:", err);
    }
}

async function updateEffectLists() {
    try {
        const raw_list = await API.getAllEffectLists();
        effect_lists = raw_list.map(item => EffectList.fromJSON(item));
    }
    catch (err) {
        console.error("Error fetching all effects:", err);
    }
}

async function uiInit() {
    try {
        await updateEffectLists();
        uiUpdatePrimaryAndSecondaryEffects();
        uiUpdateEffectListNames();

        const { name: current_list_name } = await API.getCurrentEffectListName();
        const { index: current_index } = await API.getCurrentEffectIndex();

        console.log(`Current effect list: ${current_list_name}, index: ${current_index}`);

        uiUpdateCurrentEffects(current_list_name, current_index);

    } catch (err) {
        console.error("Error initializing UI:", err);
    }
}

function uiUpdatePrimaryAndSecondaryEffects() {
    if (effect_lists.length === 0) {
        console.warn("No effect lists found. Please create a new list.");
        return;
    }

    // Extract static & dynamic effect names
    const combinedItems = [];

    for (const list of effect_lists) {
        if (list.name === "static" || list.name === "dynamic") {
            list.effects.forEach(effect => {
                combinedItems.push({
                    label: `${list.name} - ${effect.primary}`,
                    value: effect.primary
                });
            });
        }
    }

    // Populate dropdowns
    ui_primary_effect.setItems(combinedItems);

    combinedItems.unshift({
        label: "None",
        value: "None"
    });

    ui_secondary_effects.setItems(combinedItems);
}

function uiUpdateCurrentEffects(list_name, index) {
    if (!effect_lists || effect_lists.length === 0) {
        console.warn("No effect lists available.");
        return;
    }
    const current_list = effect_lists.find(l => l.name === list_name);
    if (!current_list) {
        console.warn(`Effect list '${list_name}' not found.`);
        return;
    }

    ui_current_effects.load(current_list);
    ui_current_effects.setActive(index);
    uiUpdateDeleteListButton();
}

function uiUpdateEffectListNames() {
    if (!effect_lists || effect_lists.length === 0) {
        console.warn("No effect lists available.");
        return;
    }

    const items = effect_lists.map(list => ({
        label: list.name,
        value: list.name
    }));

    ui_effect_list_names.setItems(items);
    uiUpdateDeleteListButton();
}

function uiUpdateDeleteListButton() {
    const currentListName = ui_effect_list_names.getValue();
    ui_delete_list_bt.updateDisable(currentListName);
}

function onSelectCurrentEffectListName(name) {
    try {
        API.selectEffectList(name)
        uiUpdateCurrentEffects(name, 0)
    }
    catch (err) {
        console.error("Error selecting current effect list name:", err);
    }
}

async function onClickedPreviousEffect() {
    try {
        const { index } = await API.selectPreviousEffect()
        ui_current_effects.setActive(index);
    }
    catch (err) {
        console.error("Error step to previous effect:", err);
    }
}

async function onClickedNextEffect() {
    try {
        const { index } = await API.selectNextEffect()
        ui_current_effects.setActive(index);
    }
    catch (err) {
        console.error("Error step to next effect:", err);
    }
}

function onSelectPreviewEffect() {
    try {
        const primary_effect_name = ui_primary_effect.getValue();
        const secondary_effect_name = ui_secondary_effects.getValue();
        const preview_effect = new EffectPair(
            primary_effect_name,
            secondary_effect_name === "None" ? null : secondary_effect_name
        );

        API.previewEffectPair(preview_effect)
    }
    catch (err) {
        console.error("Error selecting primary effect:", err);
    }
}


async function onCLickAddNewList() {
    const newListName = ui_new_list_name.getValue();
    if (!newListName) {
        console.warn("New effect list name cannot be empty.");
        return;
    }

    try {
        // If it was successful added, than effect list has changed, we have to reload it
        const request = new AddEffectListRequest(newListName);
        await API.addEffectList(request);
        await updateEffectLists();
        uiUpdateEffectListNames();
        ui_effect_list_names.setValue(newListName);
        uiUpdateCurrentEffects(newListName, 0);
    } catch (err) {
        console.error("Error adding new effect list:", err);
    }
}

async function onClickAddEffectToSelectedList() {
    const primaryEffectValue = ui_primary_effect.getValue();
    const secondaryEffectValue = ui_secondary_effects.getValue();
    const currentListName = ui_effect_list_names.getValue();

    if (!primaryEffectValue) {
        console.warn("Primary effect is required.");
        return;
    }

    try {
        // If it was successful added, than effect list has changed, we have to reload it
        const effectPair = new EffectPair(
            primaryEffectValue,
            secondaryEffectValue === "None" ? null : secondaryEffectValue
        );

        await API.appendEffectPairToList(currentListName, effectPair);
        await updateEffectLists();

        const currentList = effect_lists.find(list => list.name === currentListName);
        const lastIndex = currentList.effects.length - 1;

        await API.selectEffectByIndex(new SelectCurrentEffectByIndexRequest(lastIndex));

        uiUpdateEffectListNames();
        ui_effect_list_names.setValue(currentListName);
        uiUpdateCurrentEffects(currentListName, lastIndex);

    } catch (err) {
        console.error("Error adding effect pair to current list:", err);
    }
}

async function onCLickedDeleteEffect(name, primary, secondary) {
    try {
        if (secondary === "None") {
            secondary = null;
        }

        const effect_to_remove = new EffectPair(primary, secondary);
        await API.removeEffectPairFromList(name, effect_to_remove);
        await updateEffectLists();
        await API.selectEffectByIndex(new SelectCurrentEffectByIndexRequest(0));

        uiUpdateCurrentEffects(name, 0);
    } catch (err) {
        console.error("Error removing effect pair from list:", err);
    }
}

async function onClickedDeleteList() {
    const currentListName = ui_effect_list_names.getValue();
    console.log(`Deleting effect list: ${currentListName}`);

    await API.deleteEffectList(currentListName);
    await updateEffectLists();

    await API.selectEffectList("static"); // Switch to a default list after deletion
    await API.selectEffectByIndex(new SelectCurrentEffectByIndexRequest(0));

    uiUpdateEffectListNames();
    uiUpdateCurrentEffects("static", 0);
}







// OLD !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/*

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

function postAddNewList(newEffectName) {
    console.log(`Adding new effects list: ${newEffectName}`);
    fetch("/effect-list-add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name: newEffectName })
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to fetch effects list '${newEffectName}'. Status: ${res.status}`);
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
            console.error("Error loading selected effects list:", err);
        });
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

function removeEffectPairFromList(effectName, primary, secondary) {
    if (secondary === "None") {
        secondary = null;
    }

    fetch("/remove-effect-pair-from-list", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: effectName,
            primary: primary,
            secondary: secondary
        })
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Failed to remove effect pair. Status: ${res.status}`);
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
            console.error("Error removing effect pair from list:", err);
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
        */