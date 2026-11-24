// The projects page on a phone: the '95 desktop, filling the screen like an app. Its markup
// is in projects/includes/phone.html; this puts it on the page and works its windows, the
// Start menu and the taskbar. "Plain list" in the Start menu leaves it for the ordinary page.

import { isMotionOn } from "./motion.js";
import { chooseList, offerDesk } from "./list-choice.js";
import { recall, remember } from "./storage.js";

// The same key as the room's opening shot, so the desktop starts up once per visit.
const STARTED_KEY = "projects-intro";
const TIP_KEY = "projects-phone-tip";

export function startPhoneDesk(template) {
  if (!template) {
    return;
  }
  const desk = template.content.firstElementChild.cloneNode(true);
  const page = document.querySelector("[data-page]");
  const root = document.documentElement;
  document.body.append(desk);
  // Everything behind the desktop is out of reach of taps, the keyboard and screen readers.
  if (page) {
    page.inert = true;
  }

  const find = (selector) => desk.querySelector(selector);
  const files = find("[data-phone-files]");
  const filesTask = find("[data-phone-files-task]");
  const task = find("[data-phone-task]");
  const taskTitle = find("[data-phone-task-title]");
  const start = find("[data-phone-start]");
  const menu = find("[data-phone-startmenu]");
  const clock = find("[data-phone-clock]");
  const projectWindows = [
    ...desk.querySelectorAll('[data-phone-window]:not([data-phone-window="bin"])'),
  ];
  const bin = find('[data-phone-window="bin"]');

  // Starting up, once per visit and only with motion on.
  const boot = find("[data-phone-boot]");
  if (boot && isMotionOn() && recall(STARTED_KEY, { session: true }) !== "seen") {
    boot.hidden = false;
    boot.addEventListener("animationend", () => boot.remove(), { once: true });
  } else {
    boot?.remove();
  }
  remember(STARTED_KEY, "seen", { session: true });

  // The tip stays closed for the rest of the visit once it's been closed.
  const tip = find("[data-phone-tip]");
  if (tip && recall(TIP_KEY, { session: true }) === "closed") {
    tip.hidden = true;
  }

  let open = null;
  let opener = null;

  function showFiles(shown) {
    files.hidden = !shown;
    filesTask.setAttribute("aria-pressed", String(shown && open === null));
    filesTask.classList.toggle("p95-task--on", shown && open === null);
  }

  const rows = [...desk.querySelectorAll("[data-phone-project]")];

  function openProject(index, from) {
    closeMenu();
    for (const row of rows) {
      row.toggleAttribute("data-selected", Number(row.dataset.phoneProject) === index);
    }
    for (const win of projectWindows) {
      win.hidden = Number(win.dataset.phoneWindow) !== index;
    }
    open = index;
    opener = from ?? opener;
    const win = projectWindows[index];
    taskTitle.textContent = win.querySelector(".p95-win__title").textContent;
    task.hidden = false;
    showFiles(!files.hidden);
    win.querySelector("[data-phone-close]").focus();
  }

  function closeProject() {
    if (open === null) {
      return;
    }
    projectWindows[open].hidden = true;
    open = null;
    task.hidden = true;
    showFiles(true);
    opener?.focus();
  }

  function openMenu() {
    menu.hidden = false;
    start.setAttribute("aria-expanded", "true");
    menu.querySelector("a, button").focus();
  }

  function closeMenu() {
    if (!menu.hidden) {
      menu.hidden = true;
      start.setAttribute("aria-expanded", "false");
    }
  }

  function leave() {
    desk.remove();
    if (page) {
      page.inert = false;
    }
    delete root.dataset.desk;
    chooseList();
    offerDesk("phone");
    document.getElementById("projects-title")?.focus();
  }

  desk.addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) {
      if (!event.target.closest("[data-phone-startmenu]")) {
        closeMenu();
      }
      return;
    }
    if (target !== start) {
      closeMenu();
    }
    if (target.dataset.phoneProject !== undefined) {
      openProject(Number(target.dataset.phoneProject), target);
    } else if (target.hasAttribute("data-phone-next")) {
      openProject((open + 1) % projectWindows.length);
    } else if (target.hasAttribute("data-phone-close")) {
      if (!bin.hidden) {
        bin.hidden = true;
        opener?.focus();
      } else {
        closeProject();
      }
    } else if (target.dataset.phoneOpen === "bin") {
      opener = target;
      bin.hidden = false;
      bin.querySelector("[data-phone-close]").focus();
    } else if (target.hasAttribute("data-phone-minimise")) {
      showFiles(false);
      filesTask.focus();
    } else if (target === filesTask) {
      // Brings the list to the front, or puts it away if it's already there.
      if (open !== null) {
        closeProject();
      } else {
        showFiles(files.hidden);
      }
    } else if (target === start) {
      if (menu.hidden) {
        openMenu();
      } else {
        closeMenu();
      }
    } else if (target.hasAttribute("data-phone-tip-close")) {
      tip.hidden = true;
      remember(TIP_KEY, "closed", { session: true });
    } else if (target.hasAttribute("data-phone-exit")) {
      leave();
    }
  });

  desk.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    if (!menu.hidden) {
      closeMenu();
      start.focus();
    } else if (!bin.hidden) {
      bin.hidden = true;
      opener?.focus();
    } else {
      closeProject();
    }
  });

  // The taskbar clock, in the phone's own time.
  const time = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });
  const tick = () => {
    clock.textContent = time.format(new Date());
  };
  tick();
  setInterval(tick, 15000);
}
