// The one script that runs before first paint. It decides the theme, whether
// anything moves and whether the intro plays, and records them as attributes
// on <html> for the CSS and the modules to read, so the first frame is right.
(() => {
  "use strict";

  const root = document.documentElement;

  // Storage can throw, e.g. with cookies blocked, so a failed read counts as
  // nothing saved. modules/storage.js reads and writes the same keys.
  const recall = (area, key) => {
    try {
      return window[area].getItem(key);
    } catch {
      return null;
    }
  };

  if (recall("localStorage", "theme") === "light") {
    root.dataset.theme = "light";
  }

  // The animations are written for browsers from 2022 on, the same as the
  // stylesheet. Array.prototype.at arrived then, so older browsers get the
  // still site.
  const modern = "at" in Array.prototype;

  // A choice made with the motion button wins. Otherwise motion is on unless
  // the system asks for less, data saver is on, or this visit has already
  // found the device too slow. Keep in step with automaticMotion() in
  // modules/motion.js.
  const choice = recall("localStorage", "motion");
  const automatic = !(
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    navigator.connection?.saveData ||
    recall("sessionStorage", "motion-slow") === "1"
  );
  const motion = modern && (choice ? choice === "on" : automatic);
  root.dataset.motion = motion ? "on" : "off";

  // The projects page marks <html> with data-desk="available". On a screen wide enough for
  // the monitor it becomes "intro" while the opening shot is still to play this visit, and
  // "on" once it has. On a phone it becomes "phone", for the '95 desktop that fills the
  // screen. In between it goes, and the plain list of projects is shown. The keys are the
  // ones modules/desk.js and modules/list-choice.js keep.
  if (root.dataset.desk === "available") {
    const wide = modern && window.matchMedia("(min-width: 75em)").matches;
    const phone = modern && !wide && window.matchMedia("(max-width: 56em)").matches;
    if ((wide || phone) && recall("sessionStorage", "projects-view") === "list") {
      // The visitor chose the plain list earlier in this visit. data-desk-off tells
      // projects.js to offer the monitor, or the '95 desktop, back.
      delete root.dataset.desk;
      root.dataset.deskOff = wide ? "wide" : "phone";
    } else if (wide) {
      const due = motion && recall("sessionStorage", "projects-intro") !== "seen";
      root.dataset.desk = due ? "intro" : "on";
    } else if (phone) {
      root.dataset.desk = "phone";
    } else {
      delete root.dataset.desk;
    }
  }

  // Pages with an intro mark <html> as such. It plays once per visit, and only when the visit
  // starts on that page: arriving anywhere else first counts as having seen it.
  if (motion && root.dataset.intro === "available" && recall("sessionStorage", "intro-seen") !== "1") {
    root.dataset.intro = "pending";
  } else if (root.dataset.intro !== "available") {
    try {
      window.sessionStorage.setItem("intro-seen", "1");
    } catch {
      // Without storage the intro may play again, which does no harm.
    }
  }
})();
