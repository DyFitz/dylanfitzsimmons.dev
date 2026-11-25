// The wireframe sphere both globes are built on: the hero's on the home page and the one
// beside the contact form.

import { cssColour, cssValue } from "./tokens.js";

export const DEGREE = Math.PI / 180;
const TILT = 0.38;
const COS_TILT = Math.cos(TILT);
const SIN_TILT = Math.sin(TILT);

let palette = null;

// The site's colours and monospace font, read once from the CSS.
export function colours() {
  palette ??= {
    accent: cssColour("--accent-rgb"),
    text: cssColour("--screen-text-rgb"),
    mono: cssValue("--font-mono"),
  };
  return palette;
}

// Maps a latitude and longitude to [x, y, depth] on the canvas, where depth >= 0 faces the
// viewer, for a sphere turned by `rotation` and tilted towards the viewer.
export function projector(centre, radius, rotation) {
  return (lat, lon) => {
    const ring = Math.cos(lat);
    const x = ring * Math.sin(lon + rotation);
    const y = Math.sin(lat);
    const z = ring * Math.cos(lon + rotation);
    return [
      centre + radius * x,
      centre - radius * (y * COS_TILT - z * SIN_TILT),
      y * SIN_TILT + z * COS_TILT,
    ];
  };
}

// Parallels and meridians every 15 degrees, with an outline. Lines on the far side are drawn
// faintly, so the sphere reads as solid. `glow` sets the strength of each part.
export function drawSphere(context, project, centre, radius, accent, glow) {
  const front = new Path2D();
  const back = new Path2D();
  const addLine = (points) => {
    for (let i = 1; i < points.length; i += 1) {
      const a = points[i - 1];
      const b = points[i];
      const path = (a[2] + b[2]) / 2 >= 0 ? front : back;
      path.moveTo(a[0], a[1]);
      path.lineTo(b[0], b[1]);
    }
  };
  for (let lat = -75; lat <= 75; lat += 15) {
    const points = [];
    for (let lon = 0; lon <= 360; lon += 5) {
      points.push(project(lat * DEGREE, lon * DEGREE));
    }
    addLine(points);
  }
  for (let lon = 0; lon < 360; lon += 15) {
    const points = [];
    for (let lat = -90; lat <= 90; lat += 5) {
      points.push(project(lat * DEGREE, lon * DEGREE));
    }
    addLine(points);
  }

  context.lineWidth = 1;
  context.strokeStyle = accent(glow.back);
  context.stroke(back);
  context.save();
  context.shadowColor = accent(glow.halo);
  context.shadowBlur = glow.blur;
  context.strokeStyle = accent(glow.front);
  context.stroke(front);
  context.restore();

  context.lineWidth = 1.2;
  context.strokeStyle = accent(glow.outline);
  context.beginPath();
  context.arc(centre, centre, radius, 0, Math.PI * 2);
  context.stroke();
}
