// The projects page: a monitor in a room, showing the projects, with three monitors to
// choose from: a 90s desktop, an 80s terminal and a 2007 flat screen. This module holds
// everything they do: the opening shot, switching between them, their buttons and sounds,
// the two desktops with their windows, and the animated previews. The markup lives in two
// <template>s in the page, filled in by modules/template.js.

import { prepare } from "./canvas.js";
import { chooseList } from "./list-choice.js";
import { holdMeasuring } from "./animation.js";
import { isMotionOn, onMotionChange } from "./motion.js";
import { projectDrawing, readInsets } from "./project-screens.js";
import { drawRoomRain } from "./room-rain.js";
import { recall, remember } from "./storage.js";
import { mount } from "./template.js";

// The falling code behind the room: mostly ones and noughts, a good share of hexadecimal and
// symbols, and the odd katakana. modules/room-rain.js draws it, still.
function rainColumns() {
  const sets = ["01", "01", "01", "01", "01", "23456789ABCDEF", "<>/\\{}[]=+*#$%&:;?!^~|", "<>/\\{}[]=+*#$%&:;?!^~|", "アカサタナハマヤラワ"];
  const pick = (text) => text[Math.floor(Math.random() * text.length)];
  return Array.from({ length: 34 }, (_, index) => {
    const length = 14 + Math.floor(Math.random() * 17);
    const text = Array.from({ length }, () => pick(sets[Math.floor(Math.random() * sets.length)])).join("");
    return {
      text,
      left: index * 3 + Math.random() * 1.6,
      seconds: 7 + Math.random() * 9,
      delay: Math.random() * 16,
      opacity: 0.25 + Math.random() * 0.55,
    };
  });
}

export class Desk {
  constructor({ projects, urls, images, cv, picker, room, pickerTemplate, roomTemplate }) {
    this.projectList = projects;
    // The CV in brief, for the CV windows on the two desktops.
    this.cv = cv;
    this.urls = urls;
    this.images = images;
    this.mounts = [
      [pickerTemplate, picker],
      [roomTemplate, room],
    ];
    // The opening shot moves the whole page, header and footer included.
    this.page = document.querySelector("[data-page]");
    this.rain = rainColumns();
    this.previews = new WeakMap();
    this.drawings = {};
    this.state = {
      monitor: "w95",
      target: "",
      phase: "ready",
      boot: 0,
      current: 1,
      animate: isMotionOn(),
      power: "on",
      brightness: 6,
      contrast: 6,
      menu: "closed",
      menuFocus: "all",
      dial: "",
      volume: 0,
      osd: "hidden",
      osdKind: "brightness",
      signal: "ok",
      degauss: 0,
      explorer: "open",
      viewer: "open",
      media: "open",
      startOpen: false,
      query: "",
      now: Date.now(),
      saver: false,
      balloon: "",
      playing: false,
      played: 72,
      selectedIcon: "",
      pos: {
        explorer: [12.5, 4],
        viewer: [56.5, 9],
        media: [15, 79.5],
        home: [0.8, 2],
        projects: [0.8, 14],
        cv: [0.8, 26],
        contact: [0.8, 38],
        code: [0.8, 50],
        bin: [0.8, 62],
        about: [50, 7],
        paper: [28, 3],
        letter: [36, 13],
      },
      zs: { explorer: 2, viewer: 3, media: 4, about: 5, paper: 6, letter: 7 },
      about: "closed",
      // The CV document and the contact form, each a window.
      paper: "closed",
      letter: "closed",
      moving: {},
      flights: {},
      mail: "idle",
      mailNote: "",
      safe: false,
    };
    this.movingNow = {};
    this.flightsNow = {};
    this.moveTimers = {};
    this.lastActive = Date.now();
    // Once per visit, the page opens inside the screen with the monitor off.
    if (this.wantsIntro()) {
      this.state.phase = "intro";
      this.state.power = "off";
      this.state.zoom = "close";
    }
  }

  start() {
    this.values = this.renderVals();
    this.views = this.mounts.map(([template, container]) => mount(template, container, this.values));
    document.documentElement.dataset.shot = this.values.zoom;
    ["pointermove", "pointerdown", "keydown"].forEach((type) => {
      document.addEventListener(type, (event) => this.noteActivity(event), { passive: true });
    });
    onMotionChange((on) => this.setMotion(on));
    if (this.state.phase === "intro") {
      // Nothing is shown until the opening shot has been lined up on the screen.
      this.setShot({ opacity: "0" });
    }
    // head.js hid the page before first paint if the opening shot was due. From here the
    // shot keeps it hidden for as long as it needs to.
    document.documentElement.dataset.desk = "on";
    this.clock = setInterval(() => this.tick(), 1000);
    this.onResize = () => this.fitToWindow();
    // The picker is only laid out beside the room after the first measurement, so the
    // monitors' widths are checked against it again.
    requestAnimationFrame(() => {
      if (this.roomEl && !this.shotOn) {
        this.setState({ grow: this.growth(this.state.fit || 1) });
      }
    });
    window.addEventListener("resize", this.onResize);
    this.startLoop();
    if (this.state.phase === "intro") {
      this.waitToPlay();
    } else {
      this.scheduleGlitch();
    }
  }

  // The room fills the window below the heading, and the monitor is scaled to take up most of
  // its height but not all of it, so there is room around it. Nothing is measured while the
  // opening shot has the page scaled up.
  fitToWindow() {
    if (!this.roomEl || this.shotOn) {
      return;
    }
    const top = this.roomEl.getBoundingClientRect().top + window.scrollY;
    const space = Math.max(0, Math.round(window.innerHeight - top - 12));
    const fit = Math.max(0.55, Math.min(0.95, (space / 968) * 0.95));
    const grow = this.growth(fit);
    const changed = Object.keys(grow).some((key) => Math.abs(grow[key] - ((this.state.grow || {})[key] || 0)) > 0.002);
    if (changed || Math.abs(fit - (this.state.fit || 0)) > 0.005 || Math.abs(space - (this.state.space || 0)) > 2) {
      this.setState({ fit: fit, space: space, grow: grow });
    }
  }

  // How much each monitor is scaled beyond the fit. The '95 and Aero monitors are drawn up to
  // 5% larger, for their small type, and any monitor is made smaller where the window is too
  // narrow for it to clear the picker. The widths are the monitors' own, in the CSS.
  growth(fit) {
    const stage = this.roomEl.querySelector(".stage");
    const picker = document.querySelector(".page-head--monitors .picker");
    const widths = { crt: [880, 1.05], term: [940, 1], lcd: [1100, 1.05] };
    const grow = {};
    let room = Infinity;
    if (stage && picker && picker.getBoundingClientRect().width > 0) {
      const box = stage.getBoundingClientRect();
      room = 2 * (picker.getBoundingClientRect().left - 24 - (box.left + box.width / 2));
    }
    for (const [key, [width, most]] of Object.entries(widths)) {
      grow[key] = Math.max(0.6, Math.min(most, room / (width * fit)));
    }
    return grow;
  }

  // The opening shot holds on the wide view until the room is actually on screen, so it isn't
  // spent while the page is still out of sight.
  waitToPlay() {
    if (!this.roomEl || !window.IntersectionObserver) {
      this.playIntro();
      return;
    }
    this.watcher = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.3)) {
        this.watcher.disconnect();
        this.watcher = null;
        this.playIntro();
      }
    }, { threshold: [0.3] });
    this.watcher.observe(this.roomEl);
  }

  // The opening shot is remembered for the visit, so coming back to the page goes straight in.
  // It is left out altogether when motion is off.
  wantsIntro() {
    if (!isMotionOn()) {
      return false;
    }
    return recall("projects-intro", { session: true }) !== "seen";
  }

  // The page starts with the 90s screen filling the window. The monitor starts up, and the
  // camera then pulls back to the whole page.
  playIntro() {
    remember("projects-intro", "seen", { session: true });
    holdMeasuring(9000);
    clearTimeout(this.phaseTimer);
    clearInterval(this.bootTimer);
    clearTimeout(this.glitchTimer);
    this.stopTune();
    this.updateHum(false, 0);
    this.setState({ phase: "intro", power: "off", zoom: "close", boot: 0, saver: false, startOpen: false, playing: false, signal: "ok" });
    cancelAnimationFrame(this.shotFrame);
    this.shotOn = false;
    this.setState({ monitor: "w95" });
    this.setShot({ opacity: "0" });
    const run = (this.shotRun = (this.shotRun || 0) + 1);
    const begin = () => {
      if (run !== this.shotRun) {
        return;
      }
      const shot = this.closeUp();
      this.shotOn = Boolean(shot);
      this.setShot(shot || {});
      this.phaseTimer = setTimeout(() => this.boot(), 900);
    };
    // Two frames on, the 90s monitor is in place and can be measured. The shot waits for
    // its photograph as well, so the picture doesn't arrive part-way through.
    this.shotFrame = requestAnimationFrame(() => {
      this.shotFrame = requestAnimationFrame(() => {
        const photo = this.roomEl ? this.roomEl.querySelector(".pm__photo") : null;
        if (photo && photo.decode) {
          photo.decode().then(begin, begin);
        } else {
          begin();
        }
      });
    });
  }

  // Styles the page for the opening shot. Anything not given goes back to the stylesheet's.
  setShot(styles) {
    if (this.page) {
      Object.assign(this.page.style, { opacity: "", transformOrigin: "", transform: "", transition: "", ...styles });
    }
  }

  // How the page has to be moved and scaled for the monitor's screen to fill the window.
  closeUp() {
    const screen = this.roomEl ? this.roomEl.querySelector(".pm__screen") : null;
    if (!this.page || !screen) {
      return null;
    }
    const box = this.page.getBoundingClientRect();
    const glass = screen.getBoundingClientRect();
    if (!glass.width || !glass.height) {
      return null;
    }
    const wide = document.documentElement.clientWidth;
    const high = document.documentElement.clientHeight;
    // A little over, so the rounded corners of the glass are out of sight.
    const scale = Math.max(wide / glass.width, high / glass.height) * 1.1;
    const x = glass.left + glass.width / 2;
    const y = glass.top + glass.height / 2;
    this.shotOrigin = (x - box.left).toFixed(1) + "px " + (y - box.top).toFixed(1) + "px";
    this.shotTransform = "translate(" + (wide / 2 - x).toFixed(1) + "px, " + (high / 2 - y).toFixed(1) + "px) scale(" + scale.toFixed(3) + ")";
    return { transformOrigin: this.shotOrigin, transform: this.shotTransform };
  }

  endShot() {
    this.shotOn = false;
    this.setShot({});
    this.setState({ zoom: "in" });
    this.fitToWindow();
  }

  // The camera pulls back from the screen to the whole page.
  pullBack() {
    this.setState({ zoom: "pull" });
    this.setShot({
      transformOrigin: this.shotOrigin,
      transform: "translate(0px, 0px) scale(1)",
      transition: "transform 3.2s cubic-bezier(0.6, 0, 0.2, 1)",
    });
    this.phaseTimer = setTimeout(() => this.endShot(), 3300);
  }

  // Cuts the intro short and shows the page as it ends up.
  skipIntro() {
    clearTimeout(this.phaseTimer);
    clearInterval(this.bootTimer);
    cancelAnimationFrame(this.shotFrame);
    this.shotRun = (this.shotRun || 0) + 1;
    this.shotOn = false;
    this.setShot({});
    this.setState({ phase: "ready", power: "on", zoom: "in", target: "" });
    this.fitToWindow();
    this.scheduleGlitch();
  }

  // State is replaced, not changed in place, so a method holding the old state keeps a true
  // picture of how things were. The page is redrawn once after a run of changes.
  setState(patch) {
    this.state = { ...this.state, ...patch };
    if (!this.renderQueued) {
      this.renderQueued = true;
      queueMicrotask(() => {
        this.renderQueued = false;
        this.values = this.renderVals();
        this.views.forEach((update) => update(this.values));
        // The stylesheet stops the page scrolling while the opening shot has it scaled up.
        document.documentElement.dataset.shot = this.values.zoom;
      });
    }
  }

  // The site's motion button. Switching motion off part-way through the opening shot ends it.
  setMotion(on) {
    const state = this.state;
    this.setState({ animate: on });
    if (on) {
      this.startLoop();
    } else if (state.phase !== "ready") {
      this.skipIntro();
    }
  }

  // Once a second: the clocks, the media bar's time and the screensaver's idle check.
  tick() {
    const state = this.state;
    const patch = { now: Date.now() };
    if (state.playing) {
      patch.played = (state.played + 1) % 220;
    }
    // The screensaver comes on after forty seconds without the mouse moving, as on a real desktop.
    // The 90s desktop is quicker about it: twenty seconds.
    const waited = Date.now() - this.lastActive;
    const idle = (state.monitor === "glass" && waited > 40000) || (state.monitor === "w95" && waited > 20000);
    if (idle && !state.saver && state.phase === "ready" && state.power !== "off" && state.animate !== false) {
      this.saverSince = Date.now();
      this.saverPoint = null;
      patch.saver = true;
    }
    this.setState(patch);
  }

  // Three monitors, three eras. The 90s one is a CRT too, but it boots like a desktop.
  monitors() {
    return [
      { key: "w95", label: "DF 95", year: "1995", kind: "lcd" },
      { key: "green", label: "Terminal", year: "1984", kind: "crt" },
      { key: "glass", label: "Aero", year: "2007", kind: "lcd" },
    ];
  }

  kindNow() {
    const state = this.state;
    const monitor = this.monitors().find((item) => item.key === state.monitor);
    return monitor ? monitor.kind : "crt";
  }

  projects() {
    return this.projectList;
  }

  pad(value) {
    return String(value).padStart(2, "0");
  }

  clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  select(index) {
    const count = this.projects().length;
    this.setState({ current: (index + count) % count });
    const crt = this.kindNow() === "crt";
    this.tone(crt ? 988 : 1760, 0.06, crt ? "square" : "sine", 0.1);
  }

  row(project, index, current, base) {
    return Object.assign({}, project, {
      stack: project.tags.join(", "),
      lead: project.tags.length > 1 ? project.tags[0] + " +" + (project.tags.length - 1) : project.tags[0],
      isCurrent: index === current,
      isSite: project.screen === "site",
      isForecast: project.screen === "forecast",
      isBacktest: project.screen === "backtest",
      cls: index === current ? base + " " + base + "--current" : base,
      pick: (event) => {
        // A click selects the project; its write-up is a second click away, on the read button.
        if (event && event.preventDefault) {
          event.preventDefault();
        }
        this.select(index);
        // On the 2007 desktop the preview comes back if it had been closed or put away.
        const state = this.state;
        if (state.monitor === "glass" && state.viewer !== "open" && state.viewer !== "maximised" && state.viewer) {
          this.openWindow("viewer");
        }
      },
      // On the 90s desktop a double click opens the project's own window.
      open: (event) => {
        if (event && event.preventDefault) {
          event.preventDefault();
        }
        this.select(index);
        this.openWindow("about");
      },
    });
  }

  // ---------------------------------------------------------------- changing monitor

  switchTo(key) {
    const state = this.state;
    if (state.phase !== "ready" || state.monitor === key) {
      return;
    }
    this.noteActivity();
    // Changing monitor is busy for a few seconds by design, so it isn't taken as a sign of a
    // slow device.
    holdMeasuring(5000);
    this.stopTune();
    this.powerOffSound();
    this.updateHum(false, 0);
    clearTimeout(this.glitchTimer);
    this.setState({ phase: "out", target: key, power: "off", osd: "hidden", startOpen: false, saver: false, signal: "ok", playing: false, balloon: "", degauss: 0 });
    clearTimeout(this.phaseTimer);
    this.phaseTimer = setTimeout(() => {
      // Each monitor has its own knobs, so the new one starts at its usual brightness.
      this.setState({ monitor: key, phase: "in", boot: 0, brightness: 6, contrast: 6, menu: "closed", selectedIcon: "" });
      this.phaseTimer = setTimeout(() => this.boot(), 650);
    }, 760);
  }

  bootLines(key) {
    if (key === "green") {
      return ["DF SYSTEMS BIOS v1.04", "Copyright (C) 1994 DF Systems", "", "Main processor : 486DX2-66", "Memory test    : 8192K OK", "Fixed disk 0   : 540 MB", "", "Starting DF-DOS...", "C:\\> projects"];
    }
    return ["", "", "", ""];
  }

  // The new monitor switches on and shows its start-up screen, a line at a time on the CRTs.
  boot() {
    const state = this.state;
    const lines = this.bootLines(state.monitor);
    const crt = this.kindNow() === "crt";
    this.setState({ phase: "boot", boot: 0, power: "on" });
    if (crt) {
      this.powerOnSound();
      // The self test's single beep, once the memory has been counted.
      this.tone(1000, 0.2, "square", 0.12, 0, 1.2);
    }
    clearInterval(this.bootTimer);
    let step = 0;
    this.bootTimer = setInterval(() => {
      step += 1;
      if (step <= lines.length) {
        this.setState({ boot: step });
        if (crt && lines[step - 1]) {
          this.tone(1700 + Math.random() * 500, 0.012, "square", 0.03);
        }
        return;
      }
      clearInterval(this.bootTimer);
      this.phaseTimer = setTimeout(() => this.finishBoot(), crt ? 450 : 250);
    }, crt ? 210 : 650);
  }

  finishBoot() {
    const state = this.state;
    if (state.zoom === "close" && this.shotOn) {
      // The desktop is up: pull back from the screen to the whole page.
      this.setState({ phase: "ready", target: "" });
      this.pullBack();
    } else {
      this.shotOn = false;
      this.setShot({});
      this.setState({ phase: "ready", target: "", zoom: "in" });
    }
    if (this.kindNow() === "lcd") {
      this.bootSound();
    }
    this.lastActive = Date.now();
    this.updateHum(true, state.volume || 0);
    this.scheduleGlitch();
  }

  // ---------------------------------------------------------------- the monitor's buttons

  togglePower() {
    const state = this.state;
    if (state.phase !== "ready") {
      return;
    }
    const on = state.power === "off";
    this.setState({ power: on ? "on" : "off", osd: "hidden", startOpen: false, saver: false });
    if (on) {
      this.powerOnSound();
      this.scheduleGlitch();
    } else {
      this.stopTune();
      this.setState({ playing: false });
      this.powerOffSound();
    }
    this.updateHum(on, state.volume || 0);
  }

  nudge(kind, step) {
    const state = this.state;
    if (state.power === "off" || state.phase !== "ready") {
      return;
    }
    const value = this.clamp((state[kind] || 0) + step, 0, 10);
    this.setState({ [kind]: value, osd: "shown", osdKind: kind });
    clearTimeout(this.osdTimer);
    this.osdTimer = setTimeout(() => this.setState({ osd: "hidden" }), 1600);
    if (kind === "volume") {
      this.setVolume(value);
    }
    this.tone(2200, 0.025, "square", 0.04);
  }

  // The 90s monitor's own menu, drawn over the picture: brightness, contrast and volume, each
  // a bar set with the mouse. It closes itself after a few seconds left alone.
  openMenu(focus) {
    const state = this.state;
    if (state.power === "off" || state.phase !== "ready") {
      return;
    }
    this.setState({ menu: "open", menuFocus: focus === "all" ? "brightness" : focus, menuAll: focus === "all" });
    this.holdMenu();
    this.tone(1900, 0.03, "square", 0.04);
  }

  holdMenu() {
    clearTimeout(this.menuTimer);
    this.menuTimer = setTimeout(() => this.setState({ menu: "closed" }), 8000);
  }

  setLevel(kind, value) {
    const level = this.clamp(Math.round(value), 0, 10);
    if (level === this.state[kind]) {
      return;
    }
    this.setState({ [kind]: level });
    if (kind === "volume") {
      this.setVolume(level);
    }
  }

  // Pressing on a bar in the menu sets it, and dragging along it keeps setting it.
  grabBar(event, kind) {
    const track = event.currentTarget;
    const set = (e) => {
      const rect = track.getBoundingClientRect();
      this.setLevel(kind, ((e.clientX - rect.left) / rect.width) * 10);
      this.holdMenu();
    };
    const up = () => {
      window.removeEventListener("pointermove", set);
      window.removeEventListener("pointerup", up);
    };
    event.preventDefault();
    if (this.state.menuAll) {
      this.setState({ menuFocus: kind });
    }
    set(event);
    window.addEventListener("pointermove", set);
    window.addEventListener("pointerup", up);
  }

  // The terminal's two knobs: press and hold one, then move the mouse right or up to turn it
  // up, left or down to turn it down.
  barHandler(kind) {
    this.bars = this.bars || {};
    if (!this.bars[kind]) {
      this.bars[kind] = (event) => this.grabBar(event, kind);
    }
    return this.bars[kind];
  }

  dialHandler(kind) {
    this.dials = this.dials || {};
    if (!this.dials[kind]) {
      this.dials[kind] = (event) => this.startDial(event, kind);
    }
    return this.dials[kind];
  }

  startDial(event, kind) {
    const state = this.state;
    if (state.power === "off" || state.phase !== "ready") {
      return;
    }
    event.preventDefault();
    const start = typeof state[kind] === "number" ? state[kind] : 6;
    const origin = [event.clientX, event.clientY];
    this.setState({ dial: kind });
    const move = (e) => this.setLevel(kind, start + (e.clientX - origin[0] - (e.clientY - origin[1])) / 16);
    const up = () => {
      this.setState({ dial: "" });
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  shutDown() {
    const state = this.state;
    if (state.power === "off" || state.phase !== "ready") {
      return;
    }
    this.setState({ startOpen: false, safe: true });
    clearTimeout(this.safeTimer);
    this.safeTimer = setTimeout(() => {
      this.setState({ safe: false });
      this.togglePower();
    }, 2600);
  }

  degaussNow() {
    const state = this.state;
    if (state.power === "off" || state.phase !== "ready") {
      return;
    }
    this.setState({ degauss: (state.degauss || 0) + 1 });
    this.tone(62, 0.9, "sawtooth", 0.32, 48);
  }

  osdView() {
    const state = this.state;
    const kind = state.osdKind || "brightness";
    const value = kind === "volume" ? state.volume || 0 : typeof state.brightness === "number" ? state.brightness : 6;
    const segments = [];
    for (let i = 0; i < 10; i += 1) {
      segments.push({ cls: i < value ? "is-lit" : "" });
    }
    let label = kind === "volume" ? "Volume " + value : "Brightness " + value;
    if (kind === "volume" && value === 0) {
      label = "Mute";
    }
    return { label: label, segments: segments };
  }

  // ---------------------------------------------------------------- glitches

  scheduleGlitch() {
    clearTimeout(this.glitchTimer);
    if (this.kindNow() !== "crt") {
      return;
    }
    const wait = 6500 + Math.random() * 6000;
    this.glitchTimer = setTimeout(() => this.glitch(), wait);
  }

  glitch() {
    const state = this.state;
    if (state.power !== "off" && state.phase === "ready" && state.animate !== false) {
      this.setState({ signal: "glitch" });
      this.burst(0.45, 1400, 0.35);
      clearTimeout(this.signalTimer);
      this.signalTimer = setTimeout(() => this.setState({ signal: "ok" }), 560);
    }
    this.scheduleGlitch();
  }

  // ---------------------------------------------------------------- sound, made as it plays

  audio() {
    if (this.ctx) {
      return this.ctx;
    }
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) {
      return null;
    }
    const ctx = new AudioCtx();
    this.master = ctx.createGain();
    this.master.gain.value = 0;
    this.master.connect(ctx.destination);
    // A second of white noise, looped for the hiss and cut up for static.
    this.noise = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const data = this.noise.getChannelData(0);
    for (let i = 0; i < data.length; i += 1) {
      data[i] = Math.random() * 2 - 1;
    }
    this.ctx = ctx;
    return ctx;
  }

  setVolume(level) {
    const ctx = this.audio();
    if (!ctx) {
      return;
    }
    if (ctx.state === "suspended") {
      ctx.resume();
    }
    const gain = level === 0 ? 0 : Math.pow(level / 10, 2) * 0.7;
    this.master.gain.setTargetAtTime(gain, ctx.currentTime, 0.05);
    const state = this.state;
    this.updateHum(state.power !== "off" && state.phase === "ready", level);
  }

  // The tube's mains hum and the faint hiss of the picture, while it's on and the sound is up.
  updateHum(on, level) {
    const ctx = this.ctx;
    if (!ctx) {
      return;
    }
    const want = on && level > 0 && this.kindNow() === "crt";
    if (want && !this.hum) {
      const out = ctx.createGain();
      out.gain.value = 0;
      out.connect(this.master);
      const sources = [];
      [[50, 0.22], [100, 0.12], [150, 0.05]].forEach((pair) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.frequency.value = pair[0];
        gain.gain.value = pair[1];
        osc.connect(gain);
        gain.connect(out);
        osc.start();
        sources.push(osc);
      });
      const hiss = ctx.createBufferSource();
      const band = ctx.createBiquadFilter();
      const hissGain = ctx.createGain();
      hiss.buffer = this.noise;
      hiss.loop = true;
      band.type = "bandpass";
      band.frequency.value = 5200;
      band.Q.value = 0.7;
      hissGain.gain.value = 0.05;
      hiss.connect(band);
      band.connect(hissGain);
      hissGain.connect(out);
      hiss.start();
      sources.push(hiss);
      out.gain.setTargetAtTime(0.16, ctx.currentTime + 0.4, 0.3);
      this.hum = { out: out, sources: sources };
    } else if (!want && this.hum) {
      const hum = this.hum;
      hum.out.gain.setTargetAtTime(0, ctx.currentTime, 0.08);
      hum.sources.forEach((source) => source.stop(ctx.currentTime + 0.6));
      this.hum = null;
    }
  }

  tone(freq, length, type, level, slideTo, delay) {
    const ctx = this.ctx;
    const state = this.state;
    if (!ctx || !state.volume) {
      return;
    }
    const t = ctx.currentTime + (delay || 0);
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t);
    if (slideTo) {
      osc.frequency.exponentialRampToValueAtTime(slideTo, t + length);
    }
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(level, t + 0.008);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + length);
    osc.connect(gain);
    gain.connect(this.master);
    osc.start(t);
    osc.stop(t + length + 0.05);
  }

  burst(length, freq, level) {
    const ctx = this.ctx;
    const state = this.state;
    if (!ctx || !state.volume) {
      return;
    }
    const t = ctx.currentTime;
    const source = ctx.createBufferSource();
    const band = ctx.createBiquadFilter();
    const gain = ctx.createGain();
    source.buffer = this.noise;
    band.type = "bandpass";
    band.frequency.value = freq;
    band.Q.value = 0.8;
    gain.gain.setValueAtTime(level, t);
    gain.gain.setValueAtTime(level * 0.4, t + length * 0.3);
    gain.gain.setValueAtTime(level, t + length * 0.55);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + length);
    source.connect(band);
    band.connect(gain);
    gain.connect(this.master);
    source.start(t, Math.random() * 0.5);
    source.stop(t + length + 0.05);
  }

  // A soft chord, its notes a moment apart.
  chord(notes, type, level, length) {
    notes.forEach((freq, i) => this.tone(freq, length, type, level, 0, i * 0.09));
  }

  // The desktops' start-up chord, low and warm.
  bootSound() {
    this.chord([196, 293.66, 392, 493.88], "triangle", 0.08, 2.4);
  }

  powerOnSound() {
    if (this.kindNow() === "crt") {
      // The thump and buzz of the degaussing coil, then the whine of the tube warming up.
      this.tone(62, 0.9, "sawtooth", 0.32, 48);
      this.tone(320, 1.3, "sine", 0.05, 2600);
      return;
    }
    this.chord([261.63, 329.63, 392, 493.88, 587.33], "triangle", 0.09, 2.6);
  }

  powerOffSound() {
    if (this.kindNow() === "crt") {
      this.tone(1700, 0.35, "sine", 0.22, 70);
      this.burst(0.18, 3200, 0.15);
      return;
    }
    this.tone(880, 0.5, "sine", 0.12, 220);
  }

  // The media bar's tune: four chords, picked out softly, on a loop.
  startTune() {
    const ctx = this.audio();
    if (!ctx) {
      return;
    }
    if (ctx.state === "suspended") {
      ctx.resume();
    }
    const bars = [[261.63, 329.63, 392, 493.88], [220, 261.63, 329.63, 392], [174.61, 220, 261.63, 329.63], [196, 246.94, 293.66, 392]];
    const beat = 0.32;
    let step = 0;
    let next = ctx.currentTime + 0.05;
    this.stopTune();
    this.tuneTimer = setInterval(() => {
      while (next < ctx.currentTime + 0.25) {
        const bar = bars[Math.floor(step / 8) % bars.length];
        const note = bar[[0, 1, 2, 3, 2, 1, 2, 3][step % 8]] * 2;
        const delay = Math.max(0, next - ctx.currentTime);
        this.tone(note, 0.6, "sine", 0.06, 0, delay);
        this.tone(note * 2, 0.3, "triangle", 0.015, 0, delay);
        if (step % 8 === 0) {
          bar.forEach((freq) => this.tone(freq, beat * 8, "triangle", 0.02, 0, delay));
        }
        next += beat;
        step += 1;
      }
    }, 100);
  }

  stopTune() {
    clearInterval(this.tuneTimer);
    this.tuneTimer = null;
  }

  togglePlay() {
    const state = this.state;
    if (state.playing) {
      this.stopTune();
      this.setState({ playing: false });
      return;
    }
    // Playing with the sound off turns it up a little, so there's something to hear.
    if (!state.volume) {
      this.setState({ volume: 4, osd: "shown", osdKind: "volume" });
      clearTimeout(this.osdTimer);
      this.osdTimer = setTimeout(() => this.setState({ osd: "hidden" }), 1600);
      this.setVolume(4);
    }
    this.setState({ playing: true });
    this.startTune();
  }

  // ---------------------------------------------------------------- the desktops

  // Any mouse or key activity counts. Once the screensaver is up, it gets a moment's grace and
  // ignores a nudge of the mouse, so it can be watched after choosing it from the start menu.
  noteActivity(event) {
    this.lastActive = Date.now();
    const state = this.state;
    if (!state.saver) {
      return;
    }
    if (Date.now() - (this.saverSince || 0) < 1500) {
      return;
    }
    if (event && event.type === "pointermove") {
      // The 90s one stays up until something is clicked or a key is pressed.
      if (state.monitor === "w95") {
        return;
      }
      const point = [event.clientX, event.clientY];
      if (!this.saverPoint) {
        this.saverPoint = point;
        return;
      }
      if (Math.abs(point[0] - this.saverPoint[0]) + Math.abs(point[1] - this.saverPoint[1]) < 24) {
        return;
      }
    }
    this.setState({ saver: false });
  }

  startSaver() {
    this.saverSince = Date.now();
    this.saverPoint = null;
    this.setState({ startOpen: false, saver: true });
  }

  setWindow(name, value, quiet) {
    this.setState({ [name]: value, zs: this.raise(name) });
    if (!quiet) {
      this.windowSound(value === "open" || value === "maximised");
    }
  }

  windowSound(opening) {
    this.tone(opening ? 520 : 760, 0.14, "sine", 0.08, opening ? 1040 : 380);
  }

  // Marks a window as on its way out to the taskbar, back in from it, or just opened, for as
  // long as the animation runs. The times given are a little longer than the animations, which
  // hold their last frame, so a slow machine doesn't cut one short.
  setMoving(name, way, ms, done) {
    clearTimeout(this.moveTimers[name]);
    this.movingNow[name] = way;
    this.setState({ moving: Object.assign({}, this.movingNow) });
    this.moveTimers[name] = setTimeout(() => {
      delete this.movingNow[name];
      this.setState({ moving: Object.assign({}, this.movingNow) });
      if (done) {
        done();
      }
    }, ms);
  }

  // The path from a window to its button on the taskbar, as percentages so that it holds
  // whatever size the monitor is drawn at. For the 2007 desktop it is how far the window's
  // centre has to travel; for the 90s one it is where the title bar starts and ends up.
  flight(name) {
    const win = this.roomEl ? this.roomEl.querySelector('[data-win="' + name + '"]') : null;
    const task = this.roomEl ? this.roomEl.querySelector('[data-task="' + name + '"]') : null;
    const desk = win ? win.closest(".aero, .w95") : null;
    if (!win || !task || !desk) {
      return null;
    }
    const box = win.getBoundingClientRect();
    const bar = (win.querySelector(".w95-win__bar") || win).getBoundingClientRect();
    const to = task.getBoundingClientRect();
    const all = desk.getBoundingClientRect();
    if (!box.width || !box.height || !bar.width || !bar.height || !all.width) {
      return null;
    }
    const pct = (n) => (n * 100).toFixed(2) + "%";
    return {
      fly: " --to-x: " + pct((to.left + to.width / 2 - box.left - box.width / 2) / box.width) + "; --to-y: " + pct((to.top + to.height / 2 - box.top - box.height / 2) / box.height) + ";",
      strip:
        "left: " + pct((bar.left - all.left) / all.width) + "; top: " + pct((bar.top - all.top) / all.height) + "; width: " + pct(bar.width / all.width) + "; height: " + pct(bar.height / all.height) +
        "; --to-x: " + pct((to.left - bar.left) / bar.width) + "; --to-y: " + pct((to.top - bar.top) / bar.height) + "; --to-s: " + (to.width / bar.width).toFixed(3) + ";",
    };
  }

  // Minimising is animated the way each desktop did it. On the 2007 one the window shrinks
  // away into its button on the taskbar; on the 90s one the window goes at once and the
  // outline of its title bar steps down to the button.
  minimise(name) {
    const state = this.state;
    const flight = state.animate === false ? null : this.flight(name);
    if (!flight) {
      this.setWindow(name, "minimised");
      return;
    }
    this.flightsNow[name] = flight;
    this.setState({ flights: Object.assign({}, this.flightsNow), startOpen: false });
    this.windowSound(false);
    if (state.monitor === "glass") {
      this.setMoving(name, "out", 320, () => this.setWindow(name, "minimised", true));
    } else {
      this.setWindow(name, "minimised", true);
      this.setMoving(name, "out", 340);
    }
  }

  // Brings a window back from the taskbar the way it went, or simply opens it if it was closed.
  openWindow(name) {
    const state = this.state;
    const value = state[name];
    if (value === "open" || value === "maximised") {
      this.setState({ zs: this.raise(name) });
      return;
    }
    const animated = state.animate !== false;
    const flight = value === "minimised" && animated ? this.flightsNow[name] : null;
    if (state.monitor === "glass") {
      this.setWindow(name, "open");
      if (animated) {
        this.setMoving(name, flight ? "in" : "new", flight ? 320 : 260);
      }
      return;
    }
    if (!flight) {
      this.setWindow(name, "open");
      return;
    }
    this.windowSound(true);
    this.setState({ zs: this.raise(name) });
    this.setMoving(name, "in", 340, () => this.setWindow(name, "open", true));
  }

  // Brings a window to the front of the others, keeping the stacking numbers small so the
  // taskbar and start menu always stay on top.
  raise(id) {
    const zs = Object.assign({}, this.state.zs);
    const order = Object.keys(zs)
      .filter((key) => key !== id)
      .sort((a, b) => zs[a] - zs[b]);
    order.push(id);
    const next = {};
    order.forEach((key, i) => {
      next[key] = 2 + i;
    });
    return next;
  }

  windowHandlers(name) {
    const state = this.state;
    const value = state[name] || "open";
    const up = value === "open" || value === "maximised";
    return {
      minimise: () => this.minimise(name),
      maximise: () => this.setWindow(name, value === "maximised" ? "open" : "maximised"),
      close: () => this.setWindow(name, "closed"),
      task: () => (up ? this.minimise(name) : this.openWindow(name)),
      shown: up ? "true" : "false",
      value: value,
      up: up,
      inBar: value !== "closed",
      moving: (state.moving || {})[name] || "",
      place: this.placeOf(name),
      drag: this.dragHandler(name, "window"),
      front: this.frontHandler(name),
    };
  }

  placeOf(id) {
    const state = this.state;
    const at = (state.pos || {})[id] || [0, 0];
    const flight = (state.flights || {})[id];
    return "left: " + at[0] + "%; top: " + at[1] + "%; z-index: " + ((state.zs || {})[id] || 1) + ";" + (flight ? flight.fly : "");
  }

  frontHandler(id) {
    if (!this.fronts) {
      this.fronts = {};
    }
    if (!this.fronts[id]) {
      this.fronts[id] = () => this.setState({ zs: this.raise(id) });
    }
    return this.fronts[id];
  }

  // Dragging a window by its title bar, or an icon by itself, as with a mouse on a real desktop.
  dragHandler(id, kind) {
    if (!this.drags) {
      this.drags = {};
    }
    if (!this.drags[id]) {
      this.drags[id] = (event) => this.startDrag(event, id, kind);
    }
    return this.drags[id];
  }

  startDrag(event, id, kind) {
    if (event.button !== undefined && event.button !== 0) {
      return;
    }
    const target = event.target;
    if (kind === "window" && target && target.closest && target.closest("button, a, input, textarea")) {
      return;
    }
    const state = this.state;
    if (kind === "window" && state[id] === "maximised") {
      return;
    }
    const desk = event.currentTarget && event.currentTarget.closest ? event.currentTarget.closest(".aero, .w95") : null;
    if (!desk) {
      return;
    }
    event.preventDefault();
    const rect = desk.getBoundingClientRect();
    const start = (state.pos || {})[id] || [0, 0];
    const origin = [event.clientX, event.clientY];
    const patch = { selectedIcon: kind === "icon" ? id : "" };
    if (kind === "window") {
      patch.zs = this.raise(id);
    }
    this.setState(patch);
    let moved = false;
    const move = (e) => {
      if (!moved && Math.abs(e.clientX - origin[0]) + Math.abs(e.clientY - origin[1]) < 4) {
        return;
      }
      moved = true;
      const left = start[0] + ((e.clientX - origin[0]) / rect.width) * 100;
      const top = start[1] + ((e.clientY - origin[1]) / rect.height) * 100;
      this.pending = [id, [this.clamp(left, -30, 92), this.clamp(top, 0, 86)]];
      if (!this.dragFrame) {
        this.dragFrame = requestAnimationFrame(() => {
          this.dragFrame = null;
          const now = this.state || {};
          this.setState({ pos: Object.assign({}, now.pos, { [this.pending[0]]: this.pending[1] }) });
        });
      }
    };
    const up = () => {
      this.justDragged = kind === "icon" && moved;
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  // The desktop icons. Home is a link to the home page. Projects opens the projects window, as
  // this is the projects page. CV and Contact open windows of their own on the desktop; they
  // are still links underneath, for anyone opening them in a new tab. The code isn't public
  // yet, so that one says so.
  icons() {
    return [
      { key: "home", label: "Home", href: this.urls.home, live: true },
      { key: "projects", label: "Projects", href: "#", live: false },
      { key: "cv", label: "CV", href: this.urls.cv, live: false },
      { key: "contact", label: "Contact", href: this.urls.contact, live: false },
      {
        key: "code",
        label: "Source code",
        href: this.urls.source || "#",
        live: Boolean(this.urls.source),
      },
      { key: "bin", label: "Recycle Bin", href: "#", live: false },
    ];
  }

  openIcon(key) {
    if (key === "projects") {
      this.openWindow("explorer");
      return;
    }
    if (key === "cv" || key === "contact") {
      this.openWindow(key === "cv" ? "paper" : "letter");
      return;
    }
    if (key === "bin") {
      this.showBalloon("Recycle Bin: five old drafts of this page.");
      return;
    }
    this.showBalloon("The source code goes on GitHub once it has been tidied up.");
  }

  showBalloon(text) {
    this.setState({ balloon: text });
    this.tone(1320, 0.08, "sine", 0.08);
    this.tone(1760, 0.12, "sine", 0.06, 0, 0.08);
    clearTimeout(this.balloonTimer);
    this.balloonTimer = setTimeout(() => this.setState({ balloon: "" }), 4200);
  }

  showDesktop() {
    const state = this.state;
    ["explorer", "viewer", "paper", "letter"].forEach((name) => {
      const value = state[name] || "closed";
      if (value === "open" || value === "maximised") {
        this.minimise(name);
      }
    });
  }

  // The contact window is for show: nothing typed into it leaves the page or is kept. It goes
  // through the motions of sending and then owns up, with a link to the real contact page.
  sendMail(event) {
    const form = event && event.currentTarget && event.currentTarget.closest ? event.currentTarget.closest("[data-mail]") : null;
    const field = form ? form.querySelector("input") : null;
    const address = field ? field.value.trim() : "";
    if (!/^\S+@\S+\.\S+$/.test(address)) {
      this.setState({ mail: "idle", mailNote: "Type your email address first." });
      this.tone(220, 0.14, "square", 0.05);
      if (field) {
        field.focus();
      }
      return;
    }
    this.setState({ mail: "sending", mailNote: "" });
    // The sound of a number being dialled.
    [697, 852, 770, 941, 697, 852].forEach((pitch, i) => this.tone(pitch, 0.07, "sine", 0.05, 0, i * 0.11));
    clearTimeout(this.mailTimer);
    this.mailTimer = setTimeout(() => {
      this.setState({ mail: "failed" });
      this.tone(196, 0.3, "square", 0.05);
    }, 2100);
  }

  closeMail() {
    clearTimeout(this.mailTimer);
    this.setState({ mail: "idle", mailNote: "" });
  }

  // ---------------------------------------------------------------- the previews

  startLoop() {
    if (this.frame) {
      return;
    }
    const loop = (t) => {
      const state = this.state;
      if (state.animate === false) {
        this.frame = null;
        return;
      }
      // Thirty frames a second is plenty for these.
      if (!document.hidden && state.power !== "off" && state.phase === "ready" && (!this.drawnAt || t - this.drawnAt >= 33)) {
        this.drawnAt = t;
        try {
          if (state.saver && state.monitor === "w95") {
            this.drawStars(this.saverEl);
          } else {
            this.drawArt(t);
          }
        } catch (error) {
          // One bad frame shouldn't stop the loop.
        }
      }
      this.frame = requestAnimationFrame(loop);
    };
    this.frame = requestAnimationFrame(loop);
  }

  // The 90s screensaver: flying through a field of stars.
  drawStars(canvas) {
    if (!canvas) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(rect.width));
    const h = Math.max(1, Math.round(rect.height));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    const ctx = canvas.getContext("2d");
    const fresh = () => ({ x: Math.random() * 2 - 1, y: Math.random() * 2 - 1, z: 1 });
    if (!this.stars) {
      this.stars = Array.from({ length: 150 }, () => Object.assign(fresh(), { z: Math.random() }));
    }
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#fff";
    this.stars.forEach((star, i) => {
      star.z -= 0.011;
      const x = w / 2 + (star.x / star.z) * w * 0.5;
      const y = h / 2 + (star.y / star.z) * h * 0.5;
      if (star.z <= 0.02 || x < 0 || x > w || y < 0 || y > h) {
        this.stars[i] = fresh();
        return;
      }
      const size = (1 - star.z) * 2.6 + 0.6;
      ctx.fillRect(x, y, size, size);
    });
  }

  // The previews are drawn by the same module as the project cards on the home page. Each
  // canvas remembers which drawing it is showing and where the stylesheet wants it placed.
  drawArt(time) {
    const project = this.projects()[this.state.current];
    for (const canvas of [this.artEl, this.thumbEl]) {
      const art = canvas && project ? prepare(canvas) : null;
      if (!art) {
        continue;
      }
      let preview = this.previews.get(canvas);
      if (!preview || preview.screen !== project.screen) {
        this.drawings[project.screen] ??= projectDrawing(project.screen);
        preview = { screen: project.screen, draw: this.drawings[project.screen], insets: readInsets(canvas) };
        this.previews.set(canvas, preview);
      }
      preview.draw?.(art, preview.insets, time);
    }
  }

  renderVals() {
    const state = this.state;
    const animate = state.animate !== false;
    const projects = this.projects();
    const current = typeof state.current === "number" ? state.current : 1;
    const query = (state.query || "").trim().toLowerCase();
    const monitor = state.monitor || "green";
    const bright = typeof state.brightness === "number" ? state.brightness : 6;
    const contrast = typeof state.contrast === "number" ? state.contrast : 6;
    const rowBase = { glass: "files__item", w95: "w95-file" }[monitor] || "commander__row";
    // A project the search has ruled out is hidden, not removed: the templates are built once.
    const rows = projects.map((project, index) => {
      const row = this.row(project, index, current, rowBase);
      row.hidden = Boolean(query) && !(row.title + " " + row.stack).toLowerCase().includes(query);
      return row;
    });
    const now = new Date(state.now || Date.now());
    const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const osd = this.osdView();
    const explorer = this.windowHandlers("explorer");
    const viewer = this.windowHandlers("viewer");
    const about = this.windowHandlers("about");
    const cv = this.windowHandlers("paper");
    const contact = this.windowHandlers("letter");
    const moving = state.moving || {};
    // On the 90s desktop the window in front has the dark title bar.
    const front95 = [["explorer", explorer], ["about", about], ["paper", cv], ["letter", contact]]
      .filter((item) => item[1].up)
      .sort((a, b) => ((state.zs || {})[a[0]] || 0) - ((state.zs || {})[b[0]] || 0))
      .map((item) => item[0])
      .pop();
    const cls95 = (id, kind) => "w95-win w95-win--" + kind + (front95 === id ? " is-active" : "");
    // The strip that stands in for a 90s window on its way to or from the taskbar.
    const stripFor = ["explorer", "about", "paper", "letter"].find((id) => moving[id] === "out" || moving[id] === "in");
    if (!this.sendRef) {
      this.sendRef = (event) => this.sendMail(event);
      this.closeMailRef = () => this.closeMail();
    }
    if (!this.saverRef) {
      this.saverRef = (el, old) => {
        if (el || this.saverEl === old) {
          this.saverEl = el;
        }
      };
    }
    const place = (id) => this.placeOf(id);
    const lines = this.bootLines(monitor);
    const bootStep = state.phase === "boot" ? state.boot || 0 : 0;
    const played = state.played || 0;
    if (!this.artRef) {
      this.artRef = (el, old) => {
        if (el || this.artEl === old) {
          this.artEl = el;
        }
      };
      this.thumbRef = (el, old) => {
        if (el || this.thumbEl === old) {
          this.thumbEl = el;
        }
      };
      this.roomRef = (el, old) => {
        if (el || this.roomEl === old) {
          this.roomEl = el;
        }
        const canvas = el && el.querySelector(".room__rain canvas");
        if (canvas && canvas !== this.rainCanvas) {
          this.rainCanvas = canvas;
          drawRoomRain(canvas, this.rain);
        }
        this.fitToWindow();
      };
    }
    return {
      homeUrl: this.urls.home,
      cvUrl: this.urls.cv,
      contactUrl: this.urls.contact,
      sourceUrl: this.urls.source || "#",
      images: this.images,
      cv: this.cv,
      monitorOptions: this.monitors().map((item) => ({
        key: item.key,
        label: item.label,
        year: item.year,
        pressed: item.key === (state.target || monitor) ? "true" : "false",
        pick: () => this.switchTo(item.key),
      })),
      isW95: monitor === "w95",
      levels: "--bright: " + (0.4 + bright * 0.1).toFixed(2) + "; --contrast: " + (0.46 + contrast * 0.09).toFixed(2) + ";",
      menuOpen: state.menu === "open" ? "open" : "closed",
      // The first two buttons each bring up one bar; the third brings up all three and Exit.
      menuRows: [["brightness", "Brightness", bright], ["contrast", "Contrast", contrast], ["volume", "Volume", state.volume || 0]]
        .map((row) => ({
          hidden: !state.menuAll && state.menuFocus !== row[0],
          label: row[1],
          value: String(row[2] * 10),
          cls: "osd-menu__row" + (state.menuAll && state.menuFocus === row[0] ? " is-focus" : ""),
          bar: "inline-size: " + row[2] * 10 + "%;",
          grab: this.barHandler(row[0]),
        })),
      menuFull: Boolean(state.menuAll),
      menuTitle: state.menuAll ? "Monitor" : state.menuFocus === "contrast" ? "Contrast" : "Brightness",
      openBrightness: () => this.openMenu("brightness"),
      openContrast: () => this.openMenu("contrast"),
      openMenu: () => this.openMenu("all"),
      closeMenu: () => this.setState({ menu: "closed" }),
      dialBrightness: this.dialHandler("brightness"),
      dialContrast: this.dialHandler("contrast"),
      brightTurn: "--turn: " + (bright - 5) * 27 + "deg;",
      contrastTurn: "--turn: " + (contrast - 5) * 27 + "deg;",
      brightHeld: state.dial === "brightness" ? "true" : "false",
      contrastHeld: state.dial === "contrast" ? "true" : "false",
      isGreen: monitor === "green",
      isGlass: monitor === "glass",
      phase: state.phase || "ready",
      zoom: state.zoom || "in",
      fit:
        "--fit: " + (state.fit || 1).toFixed(3) + ";" +
        Object.entries(state.grow || {}).map(([key, value]) => " --grow-" + key + ": " + value.toFixed(3) + ";").join("") +
        " min-block-size: " + (state.space || 0) + "px;",
      roomRef: this.roomRef,
      // The plain list, remembered for later visits. The page reloads to it, which also
      // stops the monitor's timers and sound.
      showList: () => {
        chooseList();
        window.location.reload();
      },
      // The intro only plays with motion on, so the button is only offered then. It works at
      // any point except while the intro is already playing, including while a monitor is
      // still starting up.
      canReplay: isMotionOn(),
      replayIntro: () => {
        const now = this.state || {};
        if (isMotionOn() && now.phase !== "intro" && !this.shotOn && now.zoom !== "pull") {
          this.playIntro();
        }
      },
      bootShown: state.phase === "boot" ? "shown" : "hidden",
      bootLines: lines.map((text, i) => ({ text: text || " ", cls: i < bootStep ? "boot__line is-shown" : "boot__line" })),
      rows: rows,
      cur: this.row(projects[current], current, current, rowBase),
      count: String(projects.length),
      liveCount: String(projects.filter((project) => project.code === "WIP").length),
      toolCount: String(new Set([].concat(...projects.map((project) => project.tags))).size),
      newest: projects[0].slug,
      clock: this.pad(now.getHours()) + ":" + this.pad(now.getMinutes()),
      dateShort: this.pad(now.getDate()) + "/" + this.pad(now.getMonth() + 1) + "/" + now.getFullYear(),
      dayNumber: String(now.getDate()),
      dayName: days[now.getDay()],
      monthName: months[now.getMonth()] + " " + now.getFullYear(),
      hourDeg: String(((now.getHours() % 12) + now.getMinutes() / 60) * 30),
      minuteDeg: String((now.getMinutes() + now.getSeconds() / 60) * 6),
      secondDeg: String(now.getSeconds() * 6),
      slides: projects.map((project, index) => Object.assign(this.row(project, index, current, "slide"), {
        cls: index === Math.floor((state.now || 0) / 4000) % projects.length ? "slide is-shown" : "slide",
      })),
      prev: () => this.select(current - 1),
      next: () => this.select(current + 1),
      power: state.power === "off" ? "off" : "on",
      powerLabel: state.power === "off" ? "Switch the monitor on" : "Switch the monitor off",
      togglePower: () => this.togglePower(),
      brightnessDown: () => this.nudge("brightness", -1),
      brightnessUp: () => this.nudge("brightness", 1),
      volumeDown: () => this.nudge("volume", -1),
      volumeUp: () => this.nudge("volume", 1),
      osd: state.osd === "shown" ? "shown" : "hidden",
      osdLabel: osd.label,
      osdSegments: osd.segments,
      signal: state.signal === "glitch" ? "glitch" : "ok",
      explorerState: state.explorer || "open",
      viewerState: state.viewer || "open",
      explorerPlace: place("explorer"),
      aboutState: state.about || "closed",
      aboutPlace: place("about"),
      aboutDrag: this.dragHandler("about", "window"),
      aboutFront: () => this.setState({ zs: this.raise("about") }),
      minimiseAbout: about.minimise,
      maximiseAbout: about.maximise,
      closeAbout: about.close,
      taskAbout: about.task,
      aboutShown: about.shown,
      aboutInBar: (state.about || "closed") !== "closed",
      filesInBar: (state.explorer || "open") !== "closed",
      filesCls: cls95("explorer", "files"),
      aboutCls: cls95("about", "about"),
      cvCls: cls95("paper", "cv"),
      contactCls: cls95("letter", "mail"),
      explorerMoving: explorer.moving,
      viewerMoving: viewer.moving,
      explorerInBar: explorer.inBar,
      viewerInBar: viewer.inBar,
      cvState: cv.value,
      cvPlace: cv.place,
      cvDrag: cv.drag,
      cvFront: cv.front,
      cvMoving: cv.moving,
      minimiseCv: cv.minimise,
      maximiseCv: cv.maximise,
      closeCv: cv.close,
      taskCv: cv.task,
      cvShown: cv.shown,
      cvInBar: cv.inBar,
      contactState: contact.value,
      contactPlace: contact.place,
      contactDrag: contact.drag,
      contactFront: contact.front,
      contactMoving: contact.moving,
      minimiseContact: contact.minimise,
      maximiseContact: contact.maximise,
      closeContact: () => {
        this.closeMail();
        contact.close();
      },
      taskContact: contact.task,
      contactShown: contact.shown,
      contactInBar: contact.inBar,
      stripOn: monitor === "w95" && Boolean(stripFor),
      stripStyle: stripFor && (state.flights || {})[stripFor] ? state.flights[stripFor].strip : "",
      stripWay: stripFor ? moving[stripFor] : "",
      stripTitle: { explorer: "Projects", about: projects[current].title, paper: "cv.doc - Document", letter: "New Message" }[stripFor] || "",
      sendMail: this.sendRef,
      closeMail: this.closeMailRef,
      mailNote: state.mailNote || "",
      mailSending: state.mail === "sending",
      mailFailed: state.mail === "failed",
      mailBusy: state.mail === "idle" || !state.mail ? "false" : "true",
      mailStatus: state.mail === "sending" ? "Dialling..." : state.mail === "failed" ? "Not sent" : "Ready",
      openFiles: () => {
        this.setState({ startOpen: false });
        this.openWindow("explorer");
      },
      shutDown: () => this.shutDown(),
      safeOn: Boolean(state.safe),
      saverRef: this.saverRef,
      viewerPlace: place("viewer"),
      mediaPlace: place("media"),
      explorerDrag: this.dragHandler("explorer", "window"),
      viewerDrag: this.dragHandler("viewer", "window"),
      mediaDrag: this.dragHandler("media", "window"),
      explorerFront: () => this.setState({ zs: this.raise("explorer") }),
      viewerFront: () => this.setState({ zs: this.raise("viewer") }),
      minimiseExplorer: explorer.minimise,
      maximiseExplorer: explorer.maximise,
      closeExplorer: explorer.close,
      taskExplorer: explorer.task,
      explorerShown: explorer.shown,
      minimiseViewer: viewer.minimise,
      maximiseViewer: viewer.maximise,
      closeViewer: viewer.close,
      taskViewer: viewer.task,
      viewerShown: viewer.shown,
      showDesktop: () => this.showDesktop(),
      icons: this.icons().map((icon) => ({
        key: icon.key,
        label: icon.label,
        isHome: icon.key === "home",
        isProjects: icon.key === "projects",
        isCv: icon.key === "cv",
        isContact: icon.key === "contact",
        isCode: icon.key === "code",
        isBin: icon.key === "bin",
        cls: state.selectedIcon === icon.key ? "desk-icon is-selected" : "desk-icon",
        place: place(icon.key),
        drag: this.dragHandler(icon.key, "icon"),
        href: icon.href,
        // A click follows the link, unless the icon has just been dragged somewhere.
        press: (event) => {
          const dragged = this.justDragged;
          this.justDragged = false;
          if (dragged) {
            event.preventDefault();
            return;
          }
          if (!icon.live) {
            event.preventDefault();
            this.openIcon(icon.key);
          }
        },
      })),
      balloon: state.balloon || "",
      balloonShown: state.balloon ? "true" : "false",
      startOpen: state.startOpen ? "true" : "false",
      startExpanded: state.startOpen ? "true" : "false",
      toggleStart: () => {
        this.setState({ startOpen: !state.startOpen });
        this.tone(1320, 0.05, "sine", 0.08);
      },
      startSaver: () => this.startSaver(),
      onSearch: (event) => this.setState({ query: event && event.target ? event.target.value : "" }),
      noMatches: rows.every((row) => row.hidden),
      saverOn: Boolean(state.saver),
      playing: state.playing ? "true" : "false",
      isPlaying: Boolean(state.playing),
      isPaused: !state.playing,
      playLabel: state.playing ? "Pause" : "Play",
      togglePlay: () => this.togglePlay(),
      playedText: Math.floor(played / 60) + ":" + this.pad(played % 60) + " / 3:40",
      playedPercent: "inline-size: " + Math.round((played / 220) * 100) + "%;",
      trayVolume: () => {
        const level = state.volume ? 0 : 4;
        this.setState({ volume: level, osd: "shown", osdKind: "volume" });
        clearTimeout(this.osdTimer);
        this.osdTimer = setTimeout(() => this.setState({ osd: "hidden" }), 1600);
        this.setVolume(level);
      },
      artRef: this.artRef,
      thumbRef: this.thumbRef,
    };
  }
}
