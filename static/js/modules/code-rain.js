// The strip of falling katakana beside the globe: three columns, each with a
// bright head and a fading trail, falling at different speeds.
// static/img/code-rain.svg is a still of it, for when motion is off.

import { animate } from "./animation.js";
import { prepare } from "./canvas.js";
import { KATAKANA, randomGlyph } from "./glyphs.js";
import { cssColour, cssValue } from "./tokens.js";

const CELL = 16;
const TRAIL = 14;
const STEP_MS = 110;

let palette = null;

function colours() {
  palette ??= {
    accent: cssColour("--accent-rgb"),
    glow: cssColour("--glow-rgb"),
    font: cssValue("--font-katakana"),
  };
  return palette;
}

// Each column moves its head down a row every `every` steps.
function makeColumns() {
  const cells = () => Array.from({ length: 40 }, () => randomGlyph(KATAKANA));
  return [
    { head: 5, every: 1, count: 0, cells: cells() },
    { head: 18, every: 2, count: 0, cells: cells() },
    { head: 10, every: 3, count: 0, cells: cells() },
  ];
}

function step(columns, rows) {
  for (const column of columns) {
    column.count += 1;
    if (column.count % column.every === 0) {
      column.head = (column.head + 1) % (rows + TRAIL);
    }
    // Now and then a character changes as it falls.
    if (Math.random() < 0.35) {
      column.cells[Math.floor(Math.random() * column.cells.length)] = randomGlyph(KATAKANA);
    }
  }
}

function draw(canvas, columns) {
  const art = prepare(canvas);
  if (!art) {
    return;
  }
  const { context, width, height } = art;
  const { accent, glow, font } = colours();
  const rows = Math.floor(height / CELL);
  step(columns, rows);

  context.font = `14px ${font}`;
  context.textAlign = "center";
  context.textBaseline = "top";
  const columnWidth = width / columns.length;
  columns.forEach((column, i) => {
    const x = columnWidth * (i + 0.5);
    for (let k = 0; k < TRAIL; k += 1) {
      const row = column.head - k;
      if (row < 0 || row >= rows) {
        continue;
      }
      if (k === 0) {
        context.shadowColor = accent(0.9);
        context.shadowBlur = 8;
        context.fillStyle = glow(0.95);
      } else {
        context.shadowBlur = 0;
        context.fillStyle = accent(((1 - k / TRAIL) * 0.6).toFixed(3));
      }
      context.fillText(column.cells[row % column.cells.length], x, row * CELL);
    }
  });
  context.shadowBlur = 0;
}

export function initCodeRain(canvas) {
  if (canvas) {
    const columns = makeColumns();
    animate(canvas, () => draw(canvas, columns), { interval: STEP_MS });
  }
}
