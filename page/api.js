// Assuming EffectPair, EffectList, etc. are already defined JS classes
// Base URL is assumed to be the same origin

async function handleResponse(res) {
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
    }
    return data;
}

export const API = {

    // --- Health & Config ---
    getHealth: () => fetch("/health").then(handleResponse),

    getConfig: () => fetch("/config").then(handleResponse),

    // --- State ---
    getState: () => fetch("/state").then(handleResponse),

    setPower: (powerRequest) => fetch("/state/power", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(powerRequest)
    }).then(handleResponse),

    setBrightness: (brightnessRequest) => fetch("/state/brightness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(brightnessRequest)
    }).then(handleResponse),

    // --- Effect Lists ---
    getAllEffectLists: () => fetch("/effect-list").then(handleResponse),

    getEffectListByName: (name) => fetch(`/effect-list/${name}`).then(handleResponse),

    getEffectListNames: () => fetch("/effect-list-names").then(handleResponse),

    getCurrentEffectList: () => fetch("/effect-list-current").then(handleResponse),

    getCurrentEffectListName: () => fetch("/effect-list-current/name").then(handleResponse),

    getCurrentEffectPair: () => fetch("/effect-list-current/pair").then(handleResponse),

    getCurrentEffectIndex: () => fetch("/effect-list-current/index").then(handleResponse),

    selectNextEffect: () => fetch("/effect-list-current/next", { method: "POST" }).then(handleResponse),

    selectPreviousEffect: () => fetch("/effect-list-current/previous", { method: "POST" }).then(handleResponse),

    selectEffectByIndex: (selectCurrentEffectByIndexRequest) => fetch("/effect-list-current/index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectCurrentEffectByIndexRequest)
    }).then(handleResponse),

    addEffectList: (addEffectListRequest) => fetch("/effect-list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(addEffectListRequest)
    }).then(handleResponse),

    selectEffectList: (listName) => fetch(`/effect-list/${listName}`, {
        method: "POST"
    }).then(handleResponse),

    deleteEffectList: (listName) => fetch(`/effect-list/${listName}`, {
        method: "DELETE"
    }).then(handleResponse),

    appendEffectPairToList: (listName, effectPair) => fetch(`/effect-list/${listName}/append`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(effectPair)
    }).then(handleResponse),

    removeEffectPairFromList: (listName, effectPair) => fetch(`/effect-list/${listName}/remove`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(effectPair)
    }).then(handleResponse),

    // --- Effect Preview ---
    previewEffectPair: (effectPair) => fetch("/effect-pair/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(effectPair)
    }).then(res => res.status) // preview returns status only
};
