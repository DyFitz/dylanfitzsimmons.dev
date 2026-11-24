// The code behind the room on the projects page: columns of characters drawn once onto a
// canvas, as a still picture. It is kept still on purpose, so the browser's effort goes on the
// monitors in front. The home page has the moving version.

import { prepare } from "./canvas.js";
import { cssColour, cssValue } from "./tokens.js";

const SIZE = 18;
// How far down the room the columns can sit, in CSS pixels.
const FALL = 940;
// The rain fades out from 62% of the way down to 92%.
const FADE = [0.62, 0.92];

// Draws the columns: { text, left (%), seconds, delay, opacity }. Each column's delay places
// it somewhere along its fall, so they are scattered up and down the room.
function draw(canvas, columns, colour, font) {
  const art = prepare(canvas);
  if (!art) {
    return;
  }
  const { context, width, height } = art;
  context.font = `${SIZE}px ${font}`;
  context.textAlign = "center";
  context.textBaseline = "top";
  context.fillStyle = colour(1);
  context.shadowColor = colour(0.8);
  context.shadowBlur = 6;
  for (const column of columns) {
    const tall = column.text.length * SIZE;
    const progress = (column.delay % column.seconds) / column.seconds;
    const top = -1.05 * tall + progress * (FALL + 1.05 * tall);
    const x = (column.left / 100) * width;
    context.globalAlpha = column.opacity;
    [...column.text].forEach((glyph, i) => context.fillText(glyph, x, top + i * SIZE));
  }
  context.globalAlpha = 1;
  context.shadowBlur = 0;
  // The fade at the bottom, cut out of what was just drawn.
  const fade = context.createLinearGradient(0, 0, 0, height);
  fade.addColorStop(FADE[0], "#000");
  fade.addColorStop(FADE[1], "rgba(0, 0, 0, 0)");
  context.globalCompositeOperation = "destination-in";
  context.fillStyle = fade;
  context.fillRect(0, 0, width, height);
  context.globalCompositeOperation = "source-over";
}

// Draws the rain, and again whenever the canvas changes size or the pixel font arrives.
export function drawRoomRain(canvas, columns) {
  const colour = cssColour("--phosphor-rgb");
  const font = cssValue("--font-pixel") || "monospace";
  const redraw = () => requestAnimationFrame(() => draw(canvas, columns, colour, font));
  new ResizeObserver(redraw).observe(canvas);
  document.fonts?.load(`${SIZE}px ${font}`).then(redraw);
}
