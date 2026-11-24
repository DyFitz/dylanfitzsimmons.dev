// The small animations on the project cards, one per kind of screen:
//
//   site      this site building itself in a browser window
//   forecast  Opus Equi's chart scrolling, with a forecast fanning out ahead
//   backtest  Enular replaying a backtest and placing trades as it goes
//
// Each is drawn in the same 240 by 150 space as its still image in
// templates/core/screens, and placed by the same --art insets from main.css.

import { animate } from "./animation.js";
import { prepare } from "./canvas.js";
import { cssColour, cssValue } from "./tokens.js";

// The cards are small, so half the usual frame rate is plenty.
const FRAME_MS = 33;

let palette = null;

function colours() {
  palette ??= {
    accent: cssColour("--accent-rgb"),
    dim: cssColour("--screen-dim-rgb"),
    text: cssColour("--screen-text-rgb"),
    deep: cssValue("--screen-deep"),
    sell: cssValue("--sell"),
  };
  return palette;
}

const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

/**
 * Fits the 240 by 150 drawing space inside the screen's --art insets, keeping
 * its shape. Returns the size of one screen pixel in that space, for hairlines.
 */
function useArtSpace(art, insets) {
  const boxWidth = art.width * (1 - insets.side * 2);
  const boxHeight = art.height * (1 - insets.top - insets.bottom);
  const scale = Math.min(boxWidth / 240, boxHeight / 150);
  const left = art.width * insets.side + (boxWidth - 240 * scale) / 2;
  const top = art.height * insets.top + (boxHeight - 150 * scale) / 2;
  art.context.setTransform(art.scale * scale, 0, 0, art.scale * scale, art.scale * left, art.scale * top);
  art.context.lineCap = "round";
  art.context.lineJoin = "round";
  return 1 / scale;
}

export function readInsets(canvas) {
  const read = (name) => Number.parseFloat(cssValue(name, canvas.parentElement)) / 100 || 0;
  return { top: read("--art-top"), side: read("--art-side"), bottom: read("--art-bottom") };
}

function strokeLines(context, lines) {
  context.beginPath();
  for (const [x1, y1, x2, y2] of lines) {
    context.moveTo(x1, y1);
    context.lineTo(x2, y2);
  }
  context.stroke();
}

function polyline(context, points) {
  context.beginPath();
  points.forEach(([x, y], i) => (i === 0 ? context.moveTo(x, y) : context.lineTo(x, y)));
}

// Draws the first part of a box's outline, clockwise from the top-left corner.
function traceBox(context, x, y, width, height, progress) {
  const corners = [[x, y], [x + width, y], [x + width, y + height], [x, y + height], [x, y]];
  let left = 2 * (width + height) * progress;
  context.beginPath();
  context.moveTo(x, y);
  for (let i = 1; i < corners.length && left > 0; i += 1) {
    const [ax, ay] = corners[i - 1];
    const [bx, by] = corners[i];
    const length = Math.abs(bx - ax) + Math.abs(by - ay);
    const k = Math.min(1, left / length);
    context.lineTo(ax + (bx - ax) * k, ay + (by - ay) * k);
    left -= length;
  }
  context.stroke();
}

function drawPointer(context, x, y, pixel, outline) {
  const shape = [[0, 0], [0, 18], [5, 13], [9, 22], [12, 20.5], [8, 11.5], [15, 11.5]];
  polyline(context, shape.map(([dx, dy]) => [x + dx, y + dy]));
  context.closePath();
  context.fillStyle = "#fff";
  context.fill();
  context.lineWidth = pixel * 1.2;
  context.strokeStyle = outline;
  context.stroke();
}

// This site: the window's text types in, the project cards trace themselves,
// and a pointer clicks the first one. Loops every 7 seconds.
function drawSite(art, insets, time) {
  const { context } = art;
  const { accent, deep } = colours();
  const pixel = useArtSpace(art, insets);
  const u = (time % 7000) / 7000;
  const ramp = (from, to) => clamp((u - from) / (to - from), 0, 1);

  context.lineWidth = pixel;
  context.strokeStyle = accent(0.65);
  context.beginPath();
  if (context.roundRect) {
    context.roundRect(10, 10, 220, 130, 6);
  } else {
    context.rect(10, 10, 220, 130);
  }
  context.moveTo(10, 30);
  context.lineTo(230, 30);
  context.stroke();
  for (const x of [24, 36, 48]) {
    context.beginPath();
    context.arc(x, 20, 3, 0, Math.PI * 2);
    context.stroke();
  }

  // A small spinning globe, like the one in the hero.
  const spin = time * 0.0011;
  context.strokeStyle = accent(0.75);
  context.beginPath();
  context.arc(186, 58, 19, 0, Math.PI * 2);
  context.stroke();
  for (let k = 0; k < 4; k += 1) {
    context.beginPath();
    context.ellipse(186, 58, Math.max(0.3, Math.abs(Math.cos(spin + (k * Math.PI) / 4)) * 19), 19, 0, 0, Math.PI * 2);
    context.stroke();
  }
  strokeLines(
    context,
    [-0.5, 0, 0.5].map((lat) => {
      const half = Math.sqrt(1 - lat * lat) * 19;
      return [186 - half, 58 + lat * 19, 186 + half, 58 + lat * 19];
    }),
  );

  // The rest of the page builds up, holds, then fades out for the next loop.
  context.globalAlpha = 1 - ramp(0.9, 1);
  const bars = [
    [28, 52, 140, ramp(0.05, 0.24)],
    [28, 64, 110, ramp(0.26, 0.37)],
  ];
  context.lineWidth = 3;
  context.strokeStyle = accent(0.8);
  for (const [x, y, end, progress] of bars) {
    if (progress > 0) {
      strokeLines(context, [[x, y, x + (end - x) * progress, y]]);
    }
  }
  const typing = bars.find(([, , , progress]) => progress > 0 && progress < 1);
  if (typing && Math.floor(time / 260) % 2 === 0) {
    const [x, y, end, progress] = typing;
    context.fillStyle = accent(1);
    context.fillRect(x + (end - x) * progress + 3, y - 4, 3, 8);
  }

  context.lineWidth = pixel;
  context.strokeStyle = accent(0.65);
  [28, 92, 156].forEach((x, i) => {
    const progress = ramp(0.4 + i * 0.07, 0.47 + i * 0.07);
    if (progress > 0) {
      traceBox(context, x, 86, 56, 38, progress);
    }
  });

  // The pointer drifts over to the first card and clicks it.
  const move = ramp(0.64, 0.78);
  const eased = move * move * (3 - 2 * move);
  const click = ramp(0.78, 0.86);
  if (u >= 0.78) {
    context.fillStyle = accent(0.16);
    context.fillRect(28, 86, 56, 38);
  }
  if (click > 0 && click < 1) {
    context.strokeStyle = accent((1 - click).toFixed(3));
    context.beginPath();
    context.arc(56, 105, 4 + click * 14, 0, Math.PI * 2);
    context.stroke();
  }
  if (move > 0) {
    drawPointer(context, 205 + (52 - 205) * eased, 132 + (101 - 132) * eased, pixel, deep);
  }
  context.globalAlpha = 1;
}

// A gentle upward drift with some noise, pulled back towards the middle so it stays on the chart.
function nextValue(value) {
  const noise = (Math.random() + Math.random() + Math.random() - 1.5) * 0.09;
  return clamp(value + 0.01 + noise + (0.5 - value) * 0.08, 0.08, 0.92);
}

function makeSeries() {
  const values = [];
  let value = 0.3;
  for (let i = 0; i < 15; i += 1) {
    value = nextValue(value);
    values.push(value);
  }
  return { values, next: nextValue(value), progress: 0, last: 0 };
}

// Moves the series on by the time passed: a new point every 700ms.
function advanceSeries(series, time) {
  series.progress += clamp(time - series.last, 0, 200) / 700;
  series.last = time;
  while (series.progress >= 1) {
    series.progress -= 1;
    series.values.push(series.next);
    series.values.shift();
    series.next = nextValue(series.next);
  }
  const latest = series.values.at(-1);
  return latest + (series.next - latest) * series.progress;
}

// Opus Equi: history scrolls left a point at a time, and the forecast follows
// the recent trend, widening the further ahead it looks.
function drawForecast(art, insets, time, series) {
  const { context } = art;
  const { accent, dim, text } = colours();
  const pixel = useArtSpace(art, insets);
  const live = advanceSeries(series, time);
  const nowX = 150;
  const toY = (value) => 125 - value * 95;

  context.lineWidth = pixel * 0.8;
  context.setLineDash([2, 4]);
  context.strokeStyle = dim(0.35);
  strokeLines(context, [30, 65, 100].map((y) => [10, y, 230, y]));
  context.setLineDash([3, 3]);
  context.lineWidth = pixel;
  context.strokeStyle = text(0.35);
  strokeLines(context, [[nowX, 14, nowX, 135]]);
  context.setLineDash([]);
  context.strokeStyle = dim(0.6);
  strokeLines(context, [[10, 135, 230, 135]]);

  const count = series.values.length;
  const points = series.values.map((value, i) => [nowX - (count - 1 - i + series.progress) * 10, toY(value)]);
  points.push([nowX, toY(live)]);
  context.save();
  context.beginPath();
  context.rect(10, 0, nowX - 10, 150);
  context.clip();
  const shade = context.createLinearGradient(0, 30, 0, 135);
  shade.addColorStop(0, accent(0.2));
  shade.addColorStop(1, accent(0));
  polyline(context, [[points[0][0], 135], ...points, [nowX, 135]]);
  context.closePath();
  context.fillStyle = shade;
  context.fill();
  polyline(context, points);
  context.lineWidth = 1.6;
  context.strokeStyle = accent(1);
  context.stroke();
  context.restore();

  const recent = series.values.slice(-5);
  const trend = (recent.at(-1) - recent[0]) / (recent.length - 1);
  const nowY = toY(live);
  const endY = toY(clamp(live + trend * 5, 0.05, 0.95));
  context.save();
  context.beginPath();
  context.rect(nowX, 10, 80, 125);
  context.clip();
  context.beginPath();
  for (let i = 0; i <= 16; i += 1) {
    const k = i / 16;
    context.lineTo(nowX + 80 * k, nowY + (endY - nowY) * k - 30 * Math.sqrt(k));
  }
  for (let i = 16; i >= 0; i -= 1) {
    const k = i / 16;
    context.lineTo(nowX + 80 * k, nowY + (endY - nowY) * k + 30 * Math.sqrt(k));
  }
  context.closePath();
  context.fillStyle = accent(0.14);
  context.fill();
  context.setLineDash([0.1, 6]);
  context.lineWidth = 2.2;
  context.strokeStyle = accent(1);
  strokeLines(context, [[nowX, nowY, nowX + 80, endY]]);
  context.setLineDash([]);
  context.restore();

  const pulse = (time % 1400) / 1400;
  context.fillStyle = accent(1);
  context.beginPath();
  context.arc(nowX, nowY, 3.5, 0, Math.PI * 2);
  context.fill();
  context.lineWidth = pixel;
  context.strokeStyle = accent((1 - pulse).toFixed(3));
  context.beginPath();
  context.arc(nowX, nowY, 3.5 + pulse * 9, 0, Math.PI * 2);
  context.stroke();
}

const PRICE = [
  [6, 96], [18, 90], [30, 100], [42, 86], [54, 88], [66, 70], [78, 78], [90, 94], [102, 86], [114, 72],
  [126, 76], [138, 58], [150, 66], [162, 82], [174, 74], [186, 56], [198, 62], [210, 46], [222, 52], [234, 40],
];
const EQUITY = [
  [6, 132], [30, 131], [54, 128], [78, 124], [102, 125], [126, 120], [150, 117], [174, 118], [198, 113],
  [222, 109], [234, 107],
];
const BUYS = [[30, 100], [90, 94], [162, 82]];
const SELLS = [[66, 70], [138, 58], [210, 46]];

// The price at x, read off the line between its points.
function priceAt(x) {
  for (let i = 1; i < PRICE.length; i += 1) {
    if (x <= PRICE[i][0]) {
      const [ax, ay] = PRICE[i - 1];
      const [bx, by] = PRICE[i];
      return ay + (by - ay) * clamp((x - ax) / (bx - ax), 0, 1);
    }
  }
  return PRICE.at(-1)[1];
}

function marker(context, x, y, size, up, colour) {
  const tip = up ? -0.8 : 0.8;
  context.fillStyle = colour;
  context.beginPath();
  context.moveTo(x, y + size * tip);
  context.lineTo(x + size, y - size * tip);
  context.lineTo(x - size, y - size * tip);
  context.closePath();
  context.fill();
}

// Enular: a replay head runs through the history and the price, trades and
// equity appear as it passes. Loops every 6.5 seconds.
function drawBacktest(art, insets, time) {
  const { context } = art;
  const { accent, dim, text, sell } = colours();
  const pixel = useArtSpace(art, insets);
  const u = (time % 6500) / 6500;
  const head = 6 + 228 * Math.min(1, u / 0.78);

  context.lineWidth = pixel * 0.8;
  context.setLineDash([2, 4]);
  context.strokeStyle = dim(0.35);
  strokeLines(context, [28, 64, 100].map((y) => [6, y, 234, y]));
  context.setLineDash([]);
  context.lineWidth = pixel;
  context.strokeStyle = dim(0.6);
  strokeLines(context, [[6, 138, 234, 138]]);

  context.globalAlpha = 1 - clamp((u - 0.94) / 0.06, 0, 1);
  context.save();
  context.beginPath();
  context.rect(0, 0, head, 150);
  context.clip();
  polyline(context, PRICE);
  context.lineWidth = 1.2;
  context.strokeStyle = text(0.5);
  context.stroke();
  polyline(context, [[6, 138], ...EQUITY, [234, 138]]);
  context.closePath();
  context.fillStyle = accent(0.14);
  context.fill();
  polyline(context, EQUITY);
  context.lineWidth = 1.6;
  context.strokeStyle = accent(1);
  context.stroke();
  context.restore();

  // Trades pop in just after the head passes them: buys below the price, sells above.
  for (const [x, y] of BUYS) {
    const grow = clamp((head - x) / 10, 0, 1);
    if (grow > 0) {
      marker(context, x, y + 9, 5 * grow, true, accent(1));
    }
  }
  for (const [x, y] of SELLS) {
    const grow = clamp((head - x) / 10, 0, 1);
    if (grow > 0) {
      marker(context, x, y - 9, 5 * grow, false, sell);
    }
  }

  if (u < 0.8) {
    context.lineWidth = pixel;
    context.strokeStyle = accent(0.55);
    strokeLines(context, [[head, 18, head, 138]]);
    context.save();
    context.shadowColor = accent(0.9);
    context.shadowBlur = 8;
    context.fillStyle = accent(1);
    context.beginPath();
    context.arc(head, priceAt(head), 3, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }
  context.globalAlpha = 1;
}

const DRAWINGS = {
  site: () => drawSite,
  forecast: () => {
    const series = makeSeries();
    return (art, insets, time) => drawForecast(art, insets, time, series);
  },
  backtest: () => drawBacktest,
};

/**
 * One kind of screen's drawing, as a function of (art, insets, time), for a page that runs
 * its own loop: the monitors on the projects page do. Null if there is no such kind.
 */
export function projectDrawing(kind) {
  return DRAWINGS[kind]?.() ?? null;
}

export function initProjectScreens(canvases) {
  for (const canvas of canvases) {
    const makeDrawing = DRAWINGS[canvas.dataset.screen];
    if (!makeDrawing) {
      continue;
    }
    const drawing = makeDrawing();
    let insets = null;
    animate(
      canvas,
      (time) => {
        const art = prepare(canvas);
        if (art) {
          insets ??= readInsets(canvas);
          drawing(art, insets, time);
        }
      },
      { interval: FRAME_MS },
    );
  }
}
