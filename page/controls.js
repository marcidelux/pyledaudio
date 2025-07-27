// pico-slider.js

function createTextInput(selector, label = "Text", placeholder = "") {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="base blue row">
      <label class="base gray left flex-1">${label}</label>
      <input type="text" class="base blue interactive flex-3 left" placeholder="${placeholder}" />
    </div>
  `;

  const input = container.querySelector("input");

  return {
    getValue: () => input.value,
    setValue: (val) => { input.value = val; },
  };
}


function createSlider(selector, min = 0, max = 100, initial = 50, label = "Slider", onChange = null) {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="row base blue" style="align-items: center;">
      <span class="base left gray">${label}</span>
      <div class="base interactive button red decrement" style="width: 40px;">&lt;</div>
      <div class="base flex-4" style="padding: 0;">
        <input type="range" min="${min}" max="${max}" value="${initial}" id="slider" class="slider">
      </div>
      <div class="base interactive button green increment" style="width: 40px;">&gt;</div>
      <span class="base flex-1 value right">${initial}</span>
    </div>
  `;

  const slider = container.querySelector("#slider");
  const valueLabel = container.querySelector(".value");
  const decrementBtn = container.querySelector(".decrement");
  const incrementBtn = container.querySelector(".increment");

  let currentValue = initial;

  const updateLabel = (val) => {
    valueLabel.textContent = val;
    slider.value = val;
  };

  const updateFinal = (val) => {
    val = Math.min(max, Math.max(min, val));
    currentValue = val;
    updateLabel(val);
    if (onChange) onChange(val);
  };

  const updateTemp = (val) => {
    val = Math.min(max, Math.max(min, val));
    currentValue = val;
    updateLabel(val);
  };

  slider.addEventListener("input", () => updateTemp(parseInt(slider.value)));
  slider.addEventListener("change", () => updateFinal(parseInt(slider.value)));
  decrementBtn.addEventListener("click", () => updateFinal(parseInt(slider.value) - 1));
  incrementBtn.addEventListener("click", () => updateFinal(parseInt(slider.value) + 1));
}

function createToggleSwitch(selector, initial = false, label = "Toggle", onChange = null) {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="row base blue" style="align-items: center;">
      <div class="base left gray">${label}</div>
      <div class="base interactive button ${initial ? 'green' : 'red'} toggle-btn flex-1">
        ${initial ? 'ON' : 'OFF'}
      </div>
    </div>
  `;

  const toggleBtn = container.querySelector(".toggle-btn");
  let state = initial;

  const updateUI = () => {
    toggleBtn.classList.toggle('red', !state);
    toggleBtn.classList.toggle('green', state);
    toggleBtn.textContent = state ? 'ON' : 'OFF';
  };

  toggleBtn.addEventListener("click", () => {
    state = !state;
    updateUI();
    if (onChange) onChange(state);
  });

  updateUI(); // initialize state
}

function createButton(selector, label = "Click Me", onClick = null, color = "blue") {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="row">
      <div class="base interactive button ${color} flex-1 button-element">
        ${label}
      </div>
    </div>
  `;

  const button = container.querySelector(".button-element");
  if (onClick) {
    button.addEventListener("click", () => {
      onClick();
    });
  }
}

function createDeleteButton(selector, label = "Delete", onClick = null, color = "red") {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="row">
      <div class="base interactive button ${color} flex-1 delete-button">
        ${label}
      </div>
    </div>
  `;

  const button = container.querySelector(".delete-button");

  let currentOnClick = onClick;

  const setOnClick = (newHandler) => {
    currentOnClick = newHandler;
  };

  const updateDisable = (name) => {
    const isProtected = name === "static" || name === "dynamic";

    if (isProtected) {
      button.classList.remove("red");
      button.classList.add("gray", "disabled");
      button.textContent = "Cannot Delete";
      button.onclick = null;
    } else {
      button.classList.remove("gray", "disabled");
      button.classList.add("red");
      button.textContent = "Delete";
      button.onclick = () => {
        if (currentOnClick) currentOnClick();
      };
    }
  };

  // Initial click binding
  updateDisable("normal");

  return {
    updateDisable,
    setOnClick
  };
}


function createDropdown(selector, label = "Select", initialItems = [], onChange = null) {
  const container = document.querySelector(selector);
  if (!container) return;

  const dropdownId = selector.replace(/[^a-zA-Z0-9]/g, "") + "_select";

  container.innerHTML = `
    <div class="base blue row">
      <label class="base gray left">${label}</label>
      <select id="${dropdownId}" class="base blue interactive flex-3 left"></select>
    </div>
  `;

  const select = container.querySelector(`#${dropdownId}`);

  // Fill initial options
  initialItems.forEach(item => {
    const option = document.createElement("option");
    option.value = item.value ?? item;
    option.textContent = item.label ?? item;
    select.appendChild(option);
  });

  // Handle change
  select.addEventListener("change", () => {
    if (onChange) onChange(select.value);
  });

  // Return helper to update items later
  return {
    setItems: function (items) {
      select.innerHTML = "";
      items.forEach(item => {
        const option = document.createElement("option");
        option.value = item.value ?? item;
        option.textContent = item.label ?? item;
        select.appendChild(option);
      });
    },
    getValue: function () {
      return select.value;
    },
    setValue: function (value) {
      const option = Array.from(select.options).find(opt => opt.value === value);
      if (!option) {
        console.warn(`Option with value "${value}" not found in dropdown "${label}"`);
        return;
      }
      select.value = value;
    }
  };
}

function createEffectsListView(selector, onDelete) {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="effects-list-container base blue">
      <div class="scroll-list"></div>
    </div>
  `;

  const listContent = container.querySelector(".scroll-list");

  // Internal reference to primary/secondary elements for each row
  const rowElements = [];

  function load(data) {
    if (!data || !Array.isArray(data.effects)) return;

    listContent.innerHTML = ""; // Clear previous items
    rowElements.length = 0; // Clear stored row references

    data.effects.forEach((effect, index) => {
      const row = document.createElement("div");
      row.className = "row";

      const primary = document.createElement("div");
      primary.className = "base gray flex-2";
      primary.textContent = `${effect.primary}`;

      const secondary = document.createElement("div");
      secondary.className = "base gray flex-2";
      secondary.textContent = `${effect.secondary ?? "None"}`;

      const delBtn = document.createElement("div");
      if (data.name === "static" || data.name === "dynamic") {
        delBtn.className = "base red interactive button disabled";
        delBtn.textContent = "Cannot Delete";
      } else {
        delBtn.className = "base red interactive button";
        delBtn.textContent = "Delete";
      }

      delBtn.addEventListener("click", () => {
        onDelete(data.name, effect.primary, effect.secondary);
      });

      row.appendChild(primary);
      row.appendChild(secondary);
      row.appendChild(delBtn);
      listContent.appendChild(row);

      // Store references for highlighting later
      rowElements.push({ primary, secondary });
    });
  }

  function setActive(index) {
    console.log(`Setting active effect to index: ${index}`);
    rowElements.forEach((elements, i) => {
      const isActive = i === index;

      elements.primary.className = `base ${isActive ? 'green' : 'gray'} flex-2`;
      elements.secondary.className = `base ${isActive ? 'green' : 'gray'} flex-2`;
    });
  }

  return {
    load,
    setActive
  };
}

