// The choice between the plain list of projects and the monitor (or, on a phone, the '95
// desktop). It lasts for the visit, so each new visit starts with the monitor again. head.js
// reads the same key before first paint.

import { remember } from "./storage.js";

export const LIST_KEY = "projects-view";

export function chooseList() {
  remember(LIST_KEY, "list", { session: true });
}

// Shows the button that brings the monitor or the '95 desktop back, on the plain list.
export function offerDesk(kind) {
  const button = document.querySelector("[data-desk-back]");
  if (!button) {
    return;
  }
  button.textContent = kind === "phone" ? "back to the desktop" : "back to the monitor";
  button.hidden = false;
  button.addEventListener(
    "click",
    () => {
      remember(LIST_KEY, "desk", { session: true });
      window.location.reload();
    },
    { once: true },
  );
}
