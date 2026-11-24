// The intro: an old monitor warming up, code rain behind a boot panel that
// decrypts its checks one by one, then a scan line that wipes down the screen
// to reveal the page as it comes in. It plays once per visit, or again from
// the "replay intro" button.
//
// head.js has already decided whether it plays, and shows it before first
// paint so the page never flashes up first. Clicking it, or pressing Enter,
// Space or Escape, skips ahead.

import { animate } from "./animation.js";
import { prepare } from "./canvas.js";
import { KATAKANA, randomGlyph, scramble } from "./glyphs.js";
import { announceIntro } from "./intro-events.js";
import { isMotionOn, onMotionChange } from "./motion.js";
import { remember } from "./storage.js";
import { cssColour, cssValue } from "./tokens.js";

// Shorter on phones, where it's more in the way. Every step of the boot is timed as a share
// of it, so the whole sequence speeds up together.
const BOOT_MS = window.matchMedia("(max-width: 40em)").matches ? 2200 : 3500;
const REVEAL_MS = 900;
// The rain redraws at about 22 frames a second, like an old terminal.
const RAIN_MS = 45;
// Long enough for the last of the page's entrance animations to finish.
const ENTRANCE_MS = 2200;
const BOOT_CHECKS = [
  "power-on self test",
  "memory 65536k",
  "cpu 66mhz",
  "mounting /dev/hda1",
  "decrypting payload",
  "opening uplink",
];

let palette = null;

function colours() {
  palette ??= {
    accent: cssColour("--accent-rgb"),
    glow: cssColour("--glow-rgb"),
    tube: cssColour("--tube-rgb"),
    rec: cssColour("--rec-rgb"),
    mono: cssValue("--font-mono"),
    katakana: cssValue("--font-katakana"),
  };
  return palette;
}

// Each check is padded with dots so they all end in " ok" in the same column.
const bootLines = (columns) =>
  BOOT_CHECKS.map((check) => `${check} ${".".repeat(Math.max(3, columns - check.length - 4))} ok`);

// The tube warming up: a bright line across the middle that opens out into the screen.
function drawWarmUp(context, width, height, progress) {
  const { accent, glow, tube } = colours();
  context.fillStyle = tube(1);
  context.fillRect(0, 0, width, height);
  context.save();
  context.shadowColor = accent(0.9);
  context.shadowBlur = 24;
  if (progress < 0.5) {
    const lineWidth = width * (progress / 0.5);
    context.fillStyle = glow(0.95);
    context.fillRect((width - lineWidth) / 2, height / 2 - 1, lineWidth, 2);
  } else {
    const open = (progress - 0.5) / 0.5;
    const boxHeight = Math.max(2, height * open);
    context.fillStyle = accent((0.5 * (1 - open)).toFixed(3));
    context.fillRect(0, (height - boxHeight) / 2, width, boxHeight);
  }
  context.restore();
}

// Columns of falling katakana. Nothing is cleared between frames: a faint
// wash of the background colour fades the old characters into trails.
function drawRain(context, width, height, drops, cell) {
  const { accent, glow, tube, katakana } = colours();
  context.fillStyle = tube(0.2);
  context.fillRect(0, 0, width, height);
  context.font = `${cell - 4}px ${katakana}`;
  context.textAlign = "center";
  context.textBaseline = "top";
  for (let i = 0; i < drops.length; i += 1) {
    const y = drops[i] * cell;
    if (y >= 0) {
      context.fillStyle = Math.random() < 0.08 ? glow(0.55) : accent(0.32);
      context.fillText(randomGlyph(KATAKANA), i * cell + cell / 2, y);
    }
    drops[i] = y > height && Math.random() > 0.95 ? 0 : drops[i] + 1;
  }
}

function drawBootPanel(context, width, height, elapsed) {
  const { accent, glow, tube, mono } = colours();
  const narrow = width < 640;
  const columns = narrow ? 32 : 50;
  const padding = narrow ? 16 : 28;

  // The largest font, between 11 and 22px, that fits the panel on screen.
  let fontSize = Math.floor(
    Math.max(11, Math.min(22, (Math.min(width * 0.86, 980) - padding * 2) / (columns * 0.6))),
  );
  context.font = `${fontSize}px ${mono}`;
  let charWidth = context.measureText("0").width;
  while (fontSize > 11 && columns * charWidth + padding * 2 > width - 32) {
    fontSize -= 1;
    context.font = `${fontSize}px ${mono}`;
    charWidth = context.measureText("0").width;
  }
  const lineHeight = Math.round(fontSize * 1.7);
  const panelWidth = Math.round(columns * charWidth + padding * 2);
  const panelHeight = Math.round(lineHeight * 10 + padding * 2);
  const left = Math.round((width - panelWidth) / 2);
  const top = Math.round((height - panelHeight) / 2);

  context.save();
  context.fillStyle = tube(0.9);
  context.fillRect(left, top, panelWidth, panelHeight);
  context.shadowColor = accent(0.6);
  context.shadowBlur = 16;
  context.strokeStyle = accent(0.55);
  context.lineWidth = 1;
  context.strokeRect(left + 0.5, top + 0.5, panelWidth - 1, panelHeight - 1);
  context.restore();

  // Brackets just outside each corner.
  context.save();
  context.strokeStyle = accent(0.9);
  context.lineWidth = 2;
  const arm = 20;
  const offset = 8;
  const corners = [
    [left - offset, top - offset, 1, 1],
    [left + panelWidth + offset, top - offset, -1, 1],
    [left - offset, top + panelHeight + offset, 1, -1],
    [left + panelWidth + offset, top + panelHeight + offset, -1, -1],
  ];
  for (const [x, y, dx, dy] of corners) {
    context.beginPath();
    context.moveTo(x, y + dy * arm);
    context.lineTo(x, y);
    context.lineTo(x + dx * arm, y);
    context.stroke();
  }
  context.restore();

  const x = left + padding;
  const y = top + padding;
  const right = left + panelWidth - padding;
  const barStart = BOOT_MS * 0.74;
  const barEnd = BOOT_MS * 0.96;
  context.textBaseline = "top";
  context.textAlign = "left";
  context.fillStyle = accent(0.7);
  context.fillText("boot sequence", x, y);
  context.textAlign = "right";
  context.fillText(elapsed >= barEnd ? "ready" : "|/-\\".charAt(Math.floor(elapsed / 90) % 4), right, y);
  context.textAlign = "left";
  context.fillStyle = accent(0.25);
  context.fillRect(x, y + Math.round(lineHeight * 1.3), panelWidth - padding * 2, 1);

  // The checks decrypt one after another.
  const linesTop = y + lineHeight * 2;
  const lines = bootLines(columns);
  let cursor = null;
  lines.forEach((line, i) => {
    const begin = BOOT_MS * (0.14 + i * 0.1);
    if (elapsed < begin) {
      return;
    }
    const progress = Math.min(1, (elapsed - begin) / (BOOT_MS * 0.08));
    const rowY = linesTop + i * lineHeight;
    context.save();
    context.shadowColor = accent(0.8);
    context.shadowBlur = 10;
    context.fillStyle = progress >= 1 ? accent(1) : glow(1);
    context.fillText(scramble(line, Math.floor(progress * line.length)), x, rowY);
    context.restore();
    cursor = { x: x + (line.length + 1) * charWidth, y: rowY };
  });

  // Then a segmented loading bar.
  if (elapsed >= barStart) {
    const progress = Math.min(1, (elapsed - barStart) / (barEnd - barStart));
    const rowY = linesTop + (lines.length + 1) * lineHeight;
    context.save();
    context.shadowColor = accent(0.8);
    context.shadowBlur = 10;
    context.fillStyle = glow(1);
    context.fillText("loading", x, rowY);
    context.textAlign = "right";
    context.fillText(`${Math.floor(progress * 100)}%`, right, rowY);
    context.restore();
    const barX = x + 9 * charWidth;
    const barWidth = panelWidth - padding * 2 - 15 * charWidth;
    const segmentWidth = Math.max(5, Math.round(charWidth * 0.7));
    const gap = 3;
    const segments = Math.max(1, Math.floor((barWidth + gap) / (segmentWidth + gap)));
    const filled = Math.round(progress * segments);
    for (let s = 0; s < segments; s += 1) {
      context.fillStyle = s < filled ? accent(1) : accent(0.14);
      context.fillRect(
        barX + s * (segmentWidth + gap),
        rowY + Math.round(fontSize * 0.1),
        segmentWidth,
        Math.round(fontSize * 0.85),
      );
    }
    cursor = null;
  }
  if (cursor && Math.floor(elapsed / 270) % 2 === 0) {
    context.fillStyle = accent(1);
    context.fillRect(cursor.x, cursor.y, charWidth, fontSize);
  }
}

// Camcorder readouts in the corners: rec, a timecode, a memory address and signal bars.
function drawBootHud(context, width, height, elapsed) {
  const { accent, rec, tube, mono } = colours();
  const size = width < 640 ? 11 : 13;
  const margin = width < 640 ? 14 : 28;
  context.font = `${size}px ${mono}`;
  context.textBaseline = "top";

  const label = (text, x, y, align) => {
    const textWidth = context.measureText(text).width;
    const left = align === "right" ? x - textWidth : x;
    context.fillStyle = tube(0.85);
    context.fillRect(left - 6, y - 5, textWidth + 12, size + 10);
    context.textAlign = align;
    context.fillStyle = accent(0.85);
    context.fillText(text, x, y);
    return left;
  };
  const pad = (n) => String(n).padStart(2, "0");
  const frames = Math.floor(elapsed / 40);

  label("    rec", margin, margin, "left");
  context.fillStyle = Math.floor(elapsed / 500) % 2 === 0 ? rec(1) : rec(0.25);
  context.beginPath();
  context.arc(margin + 5, margin + size / 2, 4.5, 0, Math.PI * 2);
  context.fill();

  label(`sp 00:00:${pad(Math.floor(frames / 25) % 60)}:${pad(frames % 25)}`, width - margin, margin, "right");

  const address = Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, "0");
  label(`mem 0x${address}`, margin, height - margin - size, "left");

  const signal = Math.min(4, Math.ceil((elapsed / BOOT_MS) * 4));
  const left = label("uplink      ", width - margin, height - margin - size, "right");
  const textWidth = context.measureText("uplink ").width;
  for (let i = 0; i < 4; i += 1) {
    const barHeight = 4 + i * 3;
    context.fillStyle = i < signal ? accent(1) : accent(0.2);
    context.fillRect(left + textWidth + i * 6, height - margin - size + (size - barHeight), 4, barHeight);
  }
}

export function initIntro(button) {
  const canvas = button?.querySelector("canvas");
  if (!canvas) {
    return;
  }
  const root = document.documentElement;
  const page = document.querySelector("[data-page]");
  const replay = document.querySelector("[data-intro-replay]");

  let drops = null;
  let lastRain = -Infinity;
  let now = 0;
  let revealAt = null;
  let snapshot = null;
  let entranceTimer = 0;
  // Where focus goes back to afterwards, when the replay button started it.
  let returnFocus = null;

  const setPageInert = (inert) => {
    if (page) {
      page.inert = inert;
    }
  };

  const finish = () => {
    animation.stop();
    revealAt = null;
    snapshot = null;
    drops = null;
    // Frees the full-screen canvas's memory until it's needed again.
    canvas.width = 0;
    canvas.height = 0;
    setPageInert(false);
    root.dataset.intro = "available";
    if (returnFocus && [document.body, button].includes(document.activeElement)) {
      returnFocus.focus({ preventScroll: true });
    }
    returnFocus = null;
  };

  // Keeps the last boot frame, so the scan line can wipe it away without redrawing it.
  const startReveal = () => {
    if (revealAt !== null) {
      return;
    }
    const art = prepare(canvas, { maxScale: 1.5, clear: false });
    snapshot = null;
    if (art && canvas.width && canvas.height) {
      snapshot = document.createElement("canvas");
      snapshot.width = canvas.width;
      snapshot.height = canvas.height;
      snapshot.getContext("2d").drawImage(canvas, 0, 0);
    }
    revealAt = now;
    root.dataset.intro = "revealing";
    root.dataset.entrance = "";
    clearTimeout(entranceTimer);
    entranceTimer = setTimeout(() => delete root.dataset.entrance, ENTRANCE_MS);
    setPageInert(false);
    announceIntro("reveal");
  };

  // Above the scan line the canvas is cleared, so the page shows through; below it the last boot frame stays.
  const drawReveal = (art) => {
    const { context, width, height, scale } = art;
    const { accent, glow } = colours();
    const progress = Math.min(1, (now - revealAt) / REVEAL_MS);
    const eased = progress < 0.5 ? 2 * progress * progress : 1 - (-2 * progress + 2) ** 2 / 2;
    const lineY = eased * (height + 60);
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.clearRect(0, 0, canvas.width, canvas.height);
    const cut = Math.min(canvas.height, Math.max(0, Math.round(lineY * scale)));
    if (snapshot && cut < canvas.height && snapshot.height === canvas.height) {
      const rest = canvas.height - cut;
      context.drawImage(snapshot, 0, cut, canvas.width, rest, 0, cut, canvas.width, rest);
    }
    context.setTransform(scale, 0, 0, scale, 0, 0);
    const trail = context.createLinearGradient(0, lineY - 110, 0, lineY);
    trail.addColorStop(0, accent(0));
    trail.addColorStop(1, accent(0.3));
    context.fillStyle = trail;
    context.fillRect(0, lineY - 110, width, 110);
    context.save();
    context.shadowColor = accent(1);
    context.shadowBlur = 18;
    context.fillStyle = glow(0.95);
    context.fillRect(0, lineY - 1, width, 2);
    context.restore();
    if (progress >= 1) {
      finish();
    }
  };

  const draw = (time) => {
    now = time;
    const art = prepare(canvas, { maxScale: 1.5, clear: false });
    if (!art) {
      return;
    }
    const { context, width, height } = art;
    const cell = width < 640 ? 16 : 20;
    if (art.resized || !drops) {
      drops = Array.from({ length: Math.ceil(width / cell) }, () => -Math.floor(Math.random() * 40));
    }
    if (revealAt === null && time >= BOOT_MS) {
      startReveal();
    }
    if (revealAt !== null) {
      drawReveal(art);
      return;
    }
    const warmUp = BOOT_MS * 0.1;
    if (time < warmUp) {
      drawWarmUp(context, width, height, time / warmUp);
      return;
    }
    if (time - lastRain < RAIN_MS) {
      return;
    }
    lastRain = time;
    drawRain(context, width, height, drops, cell);
    drawBootPanel(context, width, height, time);
    drawBootHud(context, width, height, time);
  };

  const animation = animate(button, draw, { enabled: false });

  const play = () => {
    if (!isMotionOn()) {
      return;
    }
    remember("intro-seen", "1", { session: true });
    revealAt = null;
    snapshot = null;
    drops = null;
    lastRain = -Infinity;
    now = 0;
    // Ends any entrance still running, so the page comes in again after this one.
    clearTimeout(entranceTimer);
    delete root.dataset.entrance;
    root.dataset.intro = "playing";
    // The rest of the page goes inert, so the intro is the only thing Tab can reach.
    setPageInert(true);
    animation.reset();
    animation.start();
    announceIntro("start");
  };

  const skip = () => {
    if (revealAt === null) {
      startReveal();
    } else {
      finish();
    }
  };

  button.addEventListener("click", skip);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.dataset.intro === "playing") {
      skip();
    }
  });

  onMotionChange((on) => {
    if (replay) {
      replay.disabled = !on;
    }
    if (!on && ["playing", "revealing"].includes(root.dataset.intro)) {
      finish();
      delete root.dataset.entrance;
      announceIntro("reveal");
    }
  });

  if (replay) {
    replay.disabled = !isMotionOn();
    replay.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "instant" });
      returnFocus = replay;
      play();
    });
    replay.hidden = false;
  }

  if (root.dataset.intro === "pending") {
    if (getComputedStyle(button).visibility === "hidden") {
      // The fallback in main.css already hid it: the page took too long to load for an intro.
      remember("intro-seen", "1", { session: true });
      root.dataset.intro = "available";
      announceIntro("reveal");
    } else {
      play();
    }
  }
}
