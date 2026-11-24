// The readout in the header: my name, deleted a letter at a time, then each
// project typed out and deleted in turn, then a spinner and the name
// decrypting back into place, on a loop.
//
// Each step is a generator of frames, so the whole sequence reads top to
// bottom in readout() below.

import { animate } from "./animation.js";
import { scramble } from "./glyphs.js";
import { followIntro, introShowing } from "./intro-events.js";
import { isMotionOn, onMotionChange } from "./motion.js";

const PROJECTS = ["opus equi", "enular"];
const BLINK_MS = 530;
const SPINNER = "|/-\\";

// The cursor blinks while the text sits still.
function* hold(text, ms) {
  const blinks = Math.max(1, Math.round(ms / BLINK_MS));
  for (let i = 0; i < blinks; i += 1) {
    yield { text, cursor: i % 2 === 1, ms: BLINK_MS };
  }
}

function* erase(text) {
  for (let length = text.length - 1; length >= 0; length -= 1) {
    yield { text: text.slice(0, length), cursor: true, ms: 40 };
  }
  yield { text: "", cursor: true, ms: 260 };
}

// Uneven gaps between keys, like someone typing.
function* type(text) {
  for (let length = 1; length <= text.length; length += 1) {
    const ms = length === text.length ? 420 : 70 + Math.random() * 70;
    yield { text: text.slice(0, length), cursor: true, ms };
  }
}

function* spin(ms) {
  for (let elapsed = 0; elapsed < ms; elapsed += 90) {
    yield { text: SPINNER.charAt((elapsed / 90) % SPINNER.length), hot: true, ms: 90 };
  }
}

// Scrambled characters fill out to the name's length, then resolve left to right.
function* decrypt(text) {
  const fill = 10;
  const frames = 26;
  for (let frame = 1; frame < frames; frame += 1) {
    const length = Math.min(text.length, Math.ceil((frame / fill) * text.length));
    const solved = frame <= fill ? 0 : Math.floor(((frame - fill) / (frames - fill)) * text.length);
    yield { text: scramble(text.slice(0, length), solved), hot: true, ms: 50 };
  }
}

function* readout(name) {
  for (;;) {
    yield* hold(name, 2600);
    let shown = name;
    for (const project of PROJECTS) {
      yield* erase(shown);
      yield* type(project);
      yield* hold(project, 1800);
      shown = project;
    }
    yield* erase(shown);
    yield* spin(650);
    yield* decrypt(name);
  }
}

export function initBrand(link) {
  const label = link?.querySelector("[data-brand-text]");
  if (!label) {
    return;
  }
  const name = label.textContent.trim().toLowerCase();
  let frames = readout(name);
  let due = 0;

  const show = ({ text, cursor = false, hot = false }) => {
    label.textContent = text;
    link.toggleAttribute("data-cursor", cursor);
    link.toggleAttribute("data-hot", hot);
  };

  const animation = animate(
    link,
    (time) => {
      while (time >= due) {
        const frame = frames.next().value;
        show(frame);
        due += frame.ms;
      }
    },
    { enabled: false },
  );

  const start = () => {
    if (!isMotionOn() || introShowing()) {
      return;
    }
    frames = readout(name);
    due = 0;
    animation.reset();
    animation.start();
  };

  const stop = () => {
    animation.stop();
    show({ text: name });
  };

  onMotionChange((on) => (on ? start() : stop()));
  followIntro({ onStart: stop, onEnd: start });
  start();
}
