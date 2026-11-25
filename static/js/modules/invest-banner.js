// The investments banner on the home page takes turns between how the portfolio is split and
// how it has grown, every few seconds while motion is on. Choosing one with its button keeps
// it there. With motion off it stays put until a button is pressed.

import { isMotionOn, onMotionChange } from "./motion.js";

const TURN = 9000;

export function initInvestBanner(banner) {
  const switcher = banner?.querySelector("[data-banner-switch]");
  if (!switcher) {
    return;
  }
  const buttons = [...switcher.querySelectorAll("[data-banner-show]")];
  const views = new Map(
    [...banner.querySelectorAll("[data-banner-view]")].map((view) => [view.dataset.bannerView, view]),
  );
  let shown = "split";
  let chosen = false;
  let held = false;
  let timer = null;

  const show = (name) => {
    shown = name;
    for (const [key, view] of views) {
      const on = key === name;
      view.classList.toggle("is-on", on);
      view.inert = !on;
    }
    for (const button of buttons) {
      button.setAttribute("aria-pressed", String(button.dataset.bannerShow === name));
    }
  };

  // The pressed button's underline fills over each turn, so the change never comes unannounced.
  const schedule = () => {
    clearTimeout(timer);
    const running = isMotionOn() && !chosen && !held;
    switcher.toggleAttribute("data-running", running);
    if (running) {
      timer = setTimeout(() => {
        show(shown === "split" ? "growth" : "split");
        schedule();
      }, TURN);
    }
  };

  for (const button of buttons) {
    button.addEventListener("click", () => {
      chosen = true;
      show(button.dataset.bannerShow);
      schedule();
    });
  }

  // Waits while someone is reading it, pointing at it or tabbing through it.
  for (const [start, stop] of [
    ["pointerenter", "pointerleave"],
    ["focusin", "focusout"],
  ]) {
    banner.addEventListener(start, () => {
      held = true;
      schedule();
    });
    banner.addEventListener(stop, () => {
      held = false;
      schedule();
    });
  }
  document.addEventListener("visibilitychange", () => {
    held = document.hidden;
    schedule();
  });
  onMotionChange(schedule);

  switcher.hidden = false;
  show(shown);
  schedule();
}
