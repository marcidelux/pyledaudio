export class EffectPair {
    constructor(primary, secondary = null) {
        this.primary = primary;
        this.secondary = secondary;
    }

    static fromJSON(data) {
        return new EffectPair(data.primary, data.secondary);
    }

    toJSON() {
        return {
            primary: this.primary,
            secondary: this.secondary
        };
    }
}

export class EffectList {
    constructor(name, switch_interval, effects = []) {
        this.name = name;
        this.switch_interval = switch_interval;
        this.effects = effects;
    }

    static fromJSON(data) {
        const effects = Array.isArray(data.effects)
            ? data.effects.map(EffectPair.fromJSON)
            : [];
        return new EffectList(data.name, data.switch_interval, effects);
    }

    toJSON() {
        return {
            name: this.name,
            switch_interval: this.switch_interval,
            effects: this.effects.map(e => e.toJSON())
        };
    }
}

export class AddEffectListRequest {
    constructor(name, switch_interval = null, effects = null) {
        this.name = name;
        this.switch_interval = switch_interval;
        this.effects = effects;
    }

    toJSON() {
        return {
            name: this.name,
            switch_interval: this.switch_interval,
            effects: this.effects
        };
    }
}

export class SelectCurrentEffectByIndexRequest {
    constructor(index = null) {
        this.index = index;
    }

    toJSON() {
        return {
            index: this.index
        };
    }
}

export class PowerRequest {
    constructor(power = null) {
        this.power = power;
    }

    toJSON() {
        return {
            power: this.power
        };
    }
}

export class BrightnessRequest {
    constructor(brightness = null) {
        this.brightness = brightness;
    }

    toJSON() {
        return {
            brightness: this.brightness
        };
    }
}

class EffectListNamesResponse {
    constructor(list_names = []) {
        this.list_names = list_names;
    }

    static fromJSON(data) {
        return new EffectListNamesResponse(data.list_names || []);
    }

    toJSON() {
        return { list_names: this.list_names };
    }
}