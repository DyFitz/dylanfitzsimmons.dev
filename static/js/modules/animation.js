// One requestAnimationFrame loop drives every animation on the page. Each
// animation only runs while motion is on, its element is on screen and the
// tab is visible. Its clock stops while it's paused, so it carries on from
// where it was rather than jumping ahead.
//
// The loop also watches the frame rate. If the device can't keep up, the page
// switches to its still version for the rest of the visit.

import { isMotionOn, motionChosen, motionTooSlow, onMotionChange } from "./motion.js";

// Two samples in a row below this many frames a second counts as struggling.
const MIN_FPS = 20;
const SAMPLE_MS = 2000;
// A gap this long means the browser paused the page rather than fell behind.
const PAUSE_MS = 1000;
// The projects page's opening shot is heavy by design, so the frame rate isn't judged while
// it plays (data-shot is "close" or "pull"), or for this long after, while the page settles.
const SETTLE_MS = 3000;
// Caps how far a clock moves in one frame, e.g. the first frame after a pause.
const MAX_STEP_MS = 100;

const animations = new Set();
const byElement = new Map();
let frame = 0;
let lastNow = null;
let sampleStart = null;
let sampleFrames = 0;
let slowSamples = 0;
let settleUntil = 0;

const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      for (const animation of byElement.get(entry.target) ?? []) {
        animation.onScreen = entry.isIntersecting;
      }
    }
    wake();
  },
  // Starts things a little before they scroll into view, so they're never seen blank.
  { rootMargin: "200px 0px" },
);

const isRunning = (animation) =>
  animation.enabled && animation.onScreen && isMotionOn() && !document.hidden;

// Stops the frame rate being judged for a while, for something busy by design, such as
// changing monitor on the projects page.
export function holdMeasuring(ms) {
  settleUntil = Math.max(settleUntil, performance.now() + ms);
}

function measure(now, step) {
  if (motionChosen()) {
    return;
  }
  const shot = document.documentElement.dataset.shot;
  if (shot === "close" || shot === "pull") {
    settleUntil = Math.max(settleUntil, now + SETTLE_MS);
  }
  if (sampleStart === null || step > PAUSE_MS || now < settleUntil) {
    sampleStart = now;
    sampleFrames = 0;
    return;
  }
  sampleFrames += 1;
  const elapsed = now - sampleStart;
  if (elapsed < SAMPLE_MS) {
    return;
  }
  const fps = (sampleFrames * 1000) / elapsed;
  slowSamples = fps < MIN_FPS ? slowSamples + 1 : 0;
  sampleStart = now;
  sampleFrames = 0;
  if (slowSamples >= 2) {
    motionTooSlow();
  }
}

function tick(now) {
  frame = 0;
  const step = lastNow === null ? 0 : now - lastNow;
  lastNow = now;
  let ran = false;
  for (const animation of animations) {
    if (!isRunning(animation)) {
      continue;
    }
    ran = true;
    animation.time += Math.min(step, MAX_STEP_MS);
    if (animation.time - animation.drawnAt >= animation.interval) {
      animation.drawnAt = animation.time;
      try {
        animation.draw(animation.time);
      } catch (error) {
        // One broken animation shouldn't stop the rest.
        animation.enabled = false;
        console.error(error);
      }
    }
  }
  if (ran) {
    measure(now, step);
    frame = requestAnimationFrame(tick);
  } else {
    // Nothing to draw, so the loop stops until something wakes it.
    lastNow = null;
    sampleStart = null;
  }
}

function wake() {
  if (!frame && [...animations].some(isRunning)) {
    frame = requestAnimationFrame(tick);
  }
}

document.addEventListener("visibilitychange", wake);
onMotionChange(wake);

/**
 * Calls draw(time) on each frame while the animation should run. time is in
 * milliseconds and only advances while it runs. With an interval, draw is
 * called at most once per interval.
 */
export function animate(element, draw, { interval = 0, enabled = true } = {}) {
  const animation = {
    element,
    draw,
    interval,
    enabled,
    onScreen: false,
    time: 0,
    drawnAt: -Infinity,
  };
  animations.add(animation);
  if (!byElement.has(element)) {
    byElement.set(element, []);
    observer.observe(element);
  }
  byElement.get(element).push(animation);

  return {
    start() {
      animation.enabled = true;
      wake();
    },
    stop() {
      animation.enabled = false;
    },
    // Back to time 0, for animations that start over rather than carry on.
    reset() {
      animation.time = 0;
      animation.drawnAt = -Infinity;
    },
  };
}
