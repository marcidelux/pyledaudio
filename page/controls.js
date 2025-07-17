// pico-slider.js

function createSlider(selector, min = 0, max = 100, initial = 50, label = "Slider", onChange = null) {
  const container = document.querySelector(selector);
  if (!container) return;

  container.innerHTML = `
    <div class="base blue">
      <div class="row">
        <span class="base left gray">${label}</span>
        <div class="base interactive button red decrement" style="width: 40px;">&lt;</div>
        <div class="base flex-4" style="padding: 0;"><input type="range" min="${min}" max="${max}" value="${initial}" id="slider" class="slider"></div>
        <div class="base interactive button green increment" style="width: 40px;">&gt;</div>
        <span class="base flex-1 value right">${initial}</span>
      </div>
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

function createDropdown(selector, label = "Select", initialItems = [], onChange = null) {
  const container = document.querySelector(selector);
  if (!container) return;

  const dropdownId = selector.replace(/[^a-zA-Z0-9]/g, "") + "_select";

  container.innerHTML = `
    <div class="base blue row">
      <label class="base gray left">${label}</label>
      <select id="${dropdownId}" class="base blue interactive flex-2"></select>
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
        option.textContent = item.label?.toLowerCase() ?? item.toLowerCase();
        select.appendChild(option);
      });
    },
    getValue: function () {
      return select.value;
    }
  };
}

