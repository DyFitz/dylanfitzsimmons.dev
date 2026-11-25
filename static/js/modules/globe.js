// The wireframe globe in the hero: a tilted sphere of parallels and meridians
// turning slowly, with rings and ticks round it like a targeting display.
// static/img/globe.svg is its first frame, for when motion is off.

import { animate } from "./animation.js";
import { prepare } from "./canvas.js";
import { colours, DEGREE, drawSphere, projector } from "./sphere.js";

const GLOW = { back: 0.16, halo: 0.7, blur: 6, front: 0.85, outline: 0.5 };

function draw(canvas, time) {
  const art = prepare(canvas);
  if (!art) {
    return;
  }
  const { context, width: size } = art;
  const { accent, text, mono } = colours();
  const centre = size / 2;
  const radius = size * 0.32;
  const rotation = time * 0.00012;
  drawSphere(context, projector(centre, radius, rotation), centre, radius, accent, GLOW);

  // A dashed ring creeping round, and three arcs sweeping the other way.
  context.save();
  context.lineWidth = 1;
  context.setLineDash([2, 6]);
  context.lineDashOffset = -time * 0.004;
  context.strokeStyle = accent(0.45);
  context.beginPath();
  context.arc(centre, centre, radius * 1.16, 0, Math.PI * 2);
  context.stroke();
  context.restore();

  const sweep = -time * 0.00025;
  context.lineWidth = 1.6;
  context.strokeStyle = accent(0.7);
  for (let k = 0; k < 3; k += 1) {
    const start = sweep + (k * Math.PI * 2) / 3;
    context.beginPath();
    context.arc(centre, centre, radius * 1.28, start, start + 1.1);
    context.stroke();
  }

  // An outer ring of ticks, longer every 90 degrees.
  context.lineWidth = 1;
  context.strokeStyle = accent(0.18);
  context.beginPath();
  context.arc(centre, centre, radius * 1.4, 0, Math.PI * 2);
  context.stroke();
  context.strokeStyle = accent(0.5);
  for (let k = 0; k < 24; k += 1) {
    const angle = (k * Math.PI) / 12;
    const inner = radius * 1.4;
    const outer = radius * (k % 6 === 0 ? 1.49 : 1.44);
    context.beginPath();
    context.moveTo(centre + inner * Math.cos(angle), centre + inner * Math.sin(angle));
    context.lineTo(centre + outer * Math.cos(angle), centre + outer * Math.sin(angle));
    context.stroke();
  }

  // A satellite on the dashed ring.
  const orbit = time * 0.0006;
  context.save();
  context.fillStyle = accent(1);
  context.shadowColor = accent(0.9);
  context.shadowBlur = 10;
  context.beginPath();
  context.arc(
    centre + radius * 1.16 * Math.cos(orbit),
    centre + radius * 1.16 * Math.sin(orbit),
    2.6,
    0,
    Math.PI * 2,
  );
  context.fill();
  context.restore();

  const longitude = (((rotation / DEGREE) % 360) + 360) % 360;
  context.font = `11px ${mono}`;
  context.fillStyle = text(0.75);
  context.textBaseline = "alphabetic";
  context.textAlign = "right";
  context.fillText(`LON ${longitude.toFixed(1).padStart(5, "0")}°`, size - 6, size - 8);
  context.textAlign = "left";
  context.fillText("TILT 22°", 6, size - 8);
}

export function initGlobe(canvas) {
  if (canvas) {
    animate(canvas, (time) => draw(canvas, time));
  }
}
