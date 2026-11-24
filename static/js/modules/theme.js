// The day and night switch. Night is the default; head.js applies a saved
// choice before first paint.

import { remember } from "./storage.js";
import { cssValue } from "./tokens.js";

const root = document.documentElement;

export function initThemeToggle(button) {
  if (!button) {
    return;
  }
  const browserColour = document.querySelector('meta[name="theme-color"]');
  const isDay = () => root.dataset.theme === "light";

  const update = () => {
    button.textContent = isDay() ? "Switch to night" : "Switch to day";
    // Matches the browser's toolbar on phones to the page.
    browserColour?.setAttribute("content", cssValue("--page"));
  };

  button.addEventListener("click", () => {
    if (isDay()) {
      delete root.dataset.theme;
    } else {
      root.dataset.theme = "light";
    }
    remember("theme", isDay() ? "light" : "dark");
    update();
  });

  update();
  button.hidden = false;
}
