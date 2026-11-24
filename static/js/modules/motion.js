// Whether anything on the page moves. The state lives on <html> as
// data-motion, which the CSS animations hang off too, and changes are
// announced with a "motionchange" event.

import { recall, remember } from "./storage.js";

const root = document.documentElement;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

export const isMotionOn = () => root.dataset.motion === "on";

// True once the visitor has used the motion button. Their choice then beats
// the system setting and the frame-rate check.
export const motionChosen = () => recall("motion") !== null;

// The same rules head.js applies before first paint.
function automaticMotion() {
  return !(
    reducedMotion.matches ||
    navigator.connection?.saveData ||
    recall("motion-slow", { session: true }) === "1"
  );
}

function apply(on) {
  if (isMotionOn() === on) {
    return;
  }
  root.dataset.motion = on ? "on" : "off";
  document.dispatchEvent(new CustomEvent("motionchange", { detail: { on } }));
}

export function onMotionChange(callback) {
  document.addEventListener("motionchange", (event) => callback(event.detail.on));
}

// For when the device can't keep up: the page stays still for the rest of the visit. The
// projects page's monitors are the heaviest thing on the site, so struggling there only stills
// that page, not the rest of the site.
export function motionTooSlow() {
  if (!root.hasAttribute("data-desk")) {
    remember("motion-slow", "1", { session: true });
  }
  apply(false);
}

// Follows the system setting if it changes while the page is open.
export function followSystemSetting() {
  reducedMotion.addEventListener("change", () => {
    if (!motionChosen()) {
      apply(automaticMotion());
    }
  });
}

export function initMotionToggle(button) {
  if (!button) {
    return;
  }
  const update = () => button.setAttribute("aria-pressed", String(isMotionOn()));
  button.addEventListener("click", () => {
    const on = !isMotionOn();
    remember("motion", on ? "on" : "off");
    apply(on);
  });
  onMotionChange(update);
  update();
  button.hidden = false;
}
