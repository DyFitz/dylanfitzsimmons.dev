// The globe beside the contact form: the home page's wireframe globe, smaller, with Glasgow
// marked and a satellite in orbit. On the confirmation page it shows the message arriving:
// the globe turns Glasgow to the front, the packet climbs to the satellite and drops to
// Glasgow, and the pin rings out. The CSS readout beside it is timed to match.
// static/img/globe.svg stands in for it when motion is off.

import { animate } from "./animation.js";
import { prepare } from "./canvas.js";
import { cssColour, cssValue } from "./tokens.js";

const TILT = 0.38;
const DEGREE = Math.PI / 180;
const GLASGOW = { lat: 55.86 * DEGREE, lon: -4.25 * DEGREE };
// The rotation that puts Glasgow at the front.
const FACING = -GLASGOW.lon;
// Where the globe and satellite start from on the confirmation page, so the turn shows.
const SENT_START = FACING - 1.8;
const PARKED = -0.85;
const ORBIT_START = PARKED - 2.2;

// When each part of the send happens, in seconds after the page opens.
const TURN = 0.9;
const CLIMB = [0.6, 1.4];
const DROP = [1.4, 2.2];
const RINGS = 2.2;

let palette = null;

function colours() {
  palette ??= {
    accent: cssColour("--accent-rgb"),
    text: cssColour("--screen-text-rgb"),
    mono: cssValue("--font-mono"),
  };
  return palette;
}

// Eases in and out, for 0 to 1, holding at either end.
function ease(x) {
  if (x <= 0) {
    return 0;
  }
  if (x >= 1) {
    return 1;
  }
  return x < 0.5 ? 2 * x * x : 1 - (-2 * x + 2) ** 2 / 2;
}

const progress = (seconds, [start, end]) => ease((seconds - start) / (end - start));
const between = (a, b, amount) => [a[0] + (b[0] - a[0]) * amount, a[1] + (b[1] - a[1]) * amount];

function drawSphere(context, project, centre, radius, accent) {
  // Lines on the far side are drawn faintly, so the sphere reads as solid.
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
  context.strokeStyle = accent(0.14);
  context.stroke(back);
  context.save();
  context.shadowColor = accent(0.6);
  context.shadowBlur = 5;
  context.strokeStyle = accent(0.7);
  context.stroke(front);
  context.restore();

  context.lineWidth = 1.2;
  context.strokeStyle = accent(0.45);
  context.beginPath();
  context.arc(centre, centre, radius, 0, Math.PI * 2);
  context.stroke();
}

function drawSatellite(context, [x, y], accent) {
  context.save();
  context.fillStyle = accent(1);
  context.shadowColor = accent(0.9);
  context.shadowBlur = 10;
  context.fillRect(x - 5, y - 3.5, 10, 7);
  context.fillRect(x - 12, y - 1, 5, 2);
  context.fillRect(x + 7, y - 1, 5, 2);
  context.restore();
}

function drawGlasgow(context, [x, y], time, { accent, text, mono }) {
  context.fillStyle = accent(1);
  context.beginPath();
  context.arc(x, y, 3.2, 0, Math.PI * 2);
  context.fill();
  const pulse = (time % 2200) / 2200;
  context.lineWidth = 1;
  context.strokeStyle = accent(0.8 * (1 - pulse));
  context.beginPath();
  context.arc(x, y, 4 + pulse * 12, 0, Math.PI * 2);
  context.stroke();
  context.fillStyle = text(0.85);
  context.font = `11px ${mono}`;
  context.fillText("GLA", x + 8, y - 6);
}

// The packet's path: in from the corner to the satellite, then in an arc down to Glasgow,
// with three rings out from Glasgow when it lands.
function drawPacket(context, seconds, { origin, satellite, glasgow, glasgowInView }, accent) {
  const climb = progress(seconds, CLIMB);
  const drop = progress(seconds, DROP);
  const bend = [(satellite[0] + glasgow[0]) / 2 + 30, Math.min(satellite[1], glasgow[1]) - 30];
  const along = (u) => [
    (1 - u) ** 2 * satellite[0] + 2 * (1 - u) * u * bend[0] + u ** 2 * glasgow[0],
    (1 - u) ** 2 * satellite[1] + 2 * (1 - u) * u * bend[1] + u ** 2 * glasgow[1],
  ];

  context.save();
  context.lineWidth = 1;
  context.strokeStyle = accent(0.55);
  context.setLineDash([3, 4]);
  if (seconds > CLIMB[0]) {
    const end = between(origin, satellite, climb);
    context.beginPath();
    context.moveTo(...origin);
    context.lineTo(...end);
    context.stroke();
  }
  if (seconds > DROP[0]) {
    context.beginPath();
    context.moveTo(...satellite);
    for (let u = 0; u <= drop; u += 0.02) {
      context.lineTo(...along(u));
    }
    context.stroke();
  }
  context.restore();

  let dot = null;
  if (seconds > CLIMB[0] && seconds < CLIMB[1]) {
    dot = between(origin, satellite, climb);
  } else if (seconds >= DROP[0] && seconds < DROP[1]) {
    dot = along(drop);
  }
  if (dot) {
    context.save();
    context.fillStyle = "#fff";
    context.shadowColor = accent(1);
    context.shadowBlur = 14;
    context.beginPath();
    context.arc(dot[0], dot[1], 4, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }

  if (seconds > RINGS && glasgowInView) {
    context.lineWidth = 2;
    for (let k = 0; k < 3; k += 1) {
      const ring = seconds - RINGS - k * 0.18;
      if (ring > 0 && ring < 1) {
        context.strokeStyle = accent(1 - ring);
        context.beginPath();
        context.arc(glasgow[0], glasgow[1], 6 + ring * 34, 0, Math.PI * 2);
        context.stroke();
      }
    }
  }
}

function draw(canvas, time, sent) {
  const art = prepare(canvas);
  if (!art) {
    return;
  }
  const { context, width: size } = art;
  const palette = colours();
  const { accent } = palette;
  const centre = size / 2;
  const radius = size * 0.32;
  const seconds = time / 1000;

  const rotation = sent
    ? SENT_START + (FACING - SENT_START) * ease(seconds / TURN)
    : time * 0.00012;
  const cosTilt = Math.cos(TILT);
  const sinTilt = Math.sin(TILT);
  // A point on the sphere as [x, y, depth], where depth >= 0 faces the viewer.
  const project = (lat, lon) => {
    const ring = Math.cos(lat);
    const x = ring * Math.sin(lon + rotation);
    const y = Math.sin(lat);
    const z = ring * Math.cos(lon + rotation);
    return [centre + radius * x, centre - radius * (y * cosTilt - z * sinTilt), y * sinTilt + z * cosTilt];
  };

  drawSphere(context, project, centre, radius, accent);

  // The orbit, dashed and creeping round. Once a message is sent, the satellite moves to the
  // top right and holds there.
  context.save();
  context.lineWidth = 1;
  context.setLineDash([2, 6]);
  context.lineDashOffset = -time * 0.004;
  context.strokeStyle = accent(0.4);
  context.beginPath();
  context.arc(centre, centre, radius * 1.3, 0, Math.PI * 2);
  context.stroke();
  context.restore();
  const orbit = sent
    ? ORBIT_START + (PARKED - ORBIT_START) * ease(seconds / 0.6)
    : time * 0.0005;
  const satellite = [
    centre + radius * 1.3 * Math.cos(orbit),
    centre + radius * 1.3 * Math.sin(orbit),
  ];
  drawSatellite(context, satellite, accent);

  const [gx, gy, depth] = project(GLASGOW.lat, GLASGOW.lon);
  const glasgow = [gx, gy];
  const glasgowInView = depth > 0;
  if (glasgowInView) {
    drawGlasgow(context, glasgow, time, palette);
  }

  if (sent) {
    const origin = [10, size - 10];
    drawPacket(context, seconds, { origin, satellite, glasgow, glasgowInView }, accent);
  }
}

export function initUplinkGlobe(canvas) {
  if (canvas) {
    const sent = canvas.hasAttribute("data-sent");
    animate(canvas, (time) => draw(canvas, time, sent));
  }
}
