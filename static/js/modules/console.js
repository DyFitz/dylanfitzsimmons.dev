// Types out the console scripts on the home page, one after another, on a
// loop. The scripts themselves are lists in the page, the first of which is
// what shows when nothing moves.
//
// Time is counted in ticks. Commands type a character a tick, each line of
// output waits a few ticks as if the command were doing some work, and the
// finished screen holds for a while before the next script starts.

import { animate } from "./animation.js";
import { followIntro, introShowing } from "./intro-events.js";
import { isMotionOn, onMotionChange } from "./motion.js";

const TICK_MS = 45;
const OUTPUT_TICKS = 8;
// About 3.7 seconds on the finished screen.
const HOLD_TICKS = 82;
const BLINK_TICKS = 12;

function readScript(list) {
  const lines = [...list.children].map((item) => ({
    className: item.className,
    command: item.classList.contains("console__command"),
    text: item.textContent,
  }));
  // A blank line at the end for the cursor to wait on.
  lines.push({ className: "console__output", command: false, text: "" });
  return lines;
}

const typingTicks = (script) =>
  script.reduce((total, line) => total + (line.command ? line.text.length : OUTPUT_TICKS), 0);

// The lines on screen a number of ticks into a script.
function linesAt(script, ticks) {
  const lines = [];
  let remaining = ticks;
  for (const line of script) {
    if (line.command) {
      const typed = Math.max(0, Math.min(line.text.length, remaining));
      lines.push({ ...line, text: line.text.slice(0, typed) });
      remaining -= line.text.length;
      if (typed < line.text.length) {
        break;
      }
    } else {
      if (remaining < OUTPUT_TICKS) {
        break;
      }
      remaining -= OUTPUT_TICKS;
      lines.push(line);
    }
  }
  return lines;
}

function renderLine(line, { cursor = false, cursorOff = false } = {}) {
  const item = document.createElement("li");
  item.className = line.className;
  item.textContent = line.text;
  if (cursor) {
    const block = document.createElement("span");
    block.className = "console__cursor";
    block.toggleAttribute("data-off", cursorOff);
    item.append(block);
  }
  return item;
}

export function initConsole(element) {
  const screen = element?.querySelector(".console__screen");
  if (!screen) {
    return;
  }
  const stills = [...element.querySelectorAll("[data-console-script]")];
  const scripts = stills.map(readScript);
  const cycles = scripts.map((script) => typingTicks(script) + HOLD_TICKS);
  const loop = cycles.reduce((total, ticks) => total + ticks, 0);

  const live = document.createElement("ol");
  live.className = "console__script";
  live.setAttribute("role", "list");
  live.hidden = true;
  screen.append(live);

  const render = (time) => {
    let tick = Math.floor(time / TICK_MS) % loop;
    let index = 0;
    while (tick >= cycles[index]) {
      tick -= cycles[index];
      index += 1;
    }
    const script = scripts[index];
    const typed = typingTicks(script);
    const holding = tick > typed;
    const cursorOff = holding && Math.floor((tick - typed) / BLINK_TICKS) % 2 === 1;
    const lines = linesAt(script, tick);
    live.replaceChildren(
      ...lines.map((line, i) =>
        renderLine(line, { cursor: i === lines.length - 1, cursorOff }),
      ),
    );
    // Keeps the newest line in view, as a terminal would.
    screen.scrollTop = screen.scrollHeight;
  };

  const animation = animate(element, render, { interval: TICK_MS, enabled: false });

  const showLive = () => {
    for (const list of stills) {
      list.hidden = true;
    }
    live.hidden = false;
  };

  // The still version: the first script, finished.
  const showStill = () => {
    animation.stop();
    live.hidden = true;
    stills.forEach((list, i) => {
      list.hidden = i !== 0;
    });
    screen.scrollTop = 0;
  };

  // An empty prompt, waiting for the intro to finish.
  const waitAtPrompt = () => {
    animation.stop();
    showLive();
    render(0);
  };

  const start = () => {
    if (!isMotionOn() || introShowing()) {
      return;
    }
    showLive();
    animation.reset();
    animation.start();
  };

  onMotionChange((on) => (on ? start() : showStill()));
  followIntro({ onStart: waitAtPrompt, onEnd: start });

  if (!isMotionOn()) {
    showStill();
  } else if (introShowing()) {
    waitAtPrompt();
  } else {
    start();
  }
}
