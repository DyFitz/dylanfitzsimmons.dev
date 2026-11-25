// The investments page's interactive board: the dashboard and the terminal, two views of one
// state, so the date, the period, the benchmark and everything else carry over between them.
// It takes the place of the page the server sent, which stays as it is without scripts.
//
// Everything is worked out again from the data sent with the page (weights and returns only),
// for whichever day the time machine is on and whichever period is picked.

import * as m from "./invest-maths.js";
import { mount } from "./template.js";

const PERIODS = [
  { key: "1m", label: "1M" },
  { key: "3m", label: "3M" },
  { key: "ytd", label: "YTD" },
  { key: "1y", label: "1Y" },
  { key: "all", label: "All" },
];
const VIEWS = [
  { key: "perf", fn: "F1", label: "Perf" },
  { key: "risk", fn: "F2", label: "Risk" },
  { key: "alloc", fn: "F3", label: "Alloc" },
  { key: "hold", fn: "F4", label: "Hold" },
  { key: "corr", fn: "F5", label: "Corr" },
  { key: "mc", fn: "F6", label: "MC" },
  { key: "stress", fn: "F7", label: "Stress" },
  { key: "trades", fn: "F8", label: "Trades" },
  { key: "notes", fn: "F9", label: "Notes" },
];
const ALLOC_BY = [
  { key: "sleeve", label: "Sleeve" },
  { key: "sector", label: "Sector" },
  { key: "region", label: "Region" },
  { key: "asset", label: "Asset class" },
  { key: "currency", label: "Currency" },
];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const EQUITY_SLEEVES = new Set(["growth", "income", "defensive"]);
// The rationale's sell-off scenarios. Each move can be changed with its slider.
const SCENARIOS = [
  { key: "chips", label: "Chips", move: -0.4, min: -60, max: 40, picks: (h) => h.sector === "Semiconductors" },
  { key: "memory", label: "Memory", move: -0.5, min: -70, max: 50, picks: (h) => h.ticker === "MU" || h.ticker === "SKHY" },
  { key: "gold", label: "Gold", move: -0.2, min: -40, max: 30, picks: (h) => h.sector === "Gold" },
  { key: "shares", label: "All shares", move: -0.25, min: -50, max: 30, picks: (h) => EQUITY_SLEEVES.has(h.sleeve) },
];
// Examples for the world shares and chips sliders, from the design.
const PRESETS = [
  { label: "Sell-off", shock: -0.1, chips: -0.05 },
  { label: "Bear market", shock: -0.25, chips: -0.15 },
  { label: "Chip slump", shock: -0.05, chips: -0.25 },
  { label: "Rally", shock: 0.15, chips: 0.1 },
];
const CHIPS_FUND = "SEMI";
const DASH = "–";

const pct = (x, dp = 1, signed = true) => {
  if (x === null || x === undefined || !Number.isFinite(x)) return DASH;
  const shown = Number((x * 100).toFixed(dp)) + 0;
  return (signed && shown > 0 ? "+" : "") + shown.toFixed(dp) + "%";
};
const num = (x, dp = 2) => (x === null || x === undefined || !Number.isFinite(x) ? DASH : x.toFixed(dp));
const tone = (x) => (x === null || x === undefined ? "iv-flat" : x > 0.00005 ? "iv-up" : x < -0.00005 ? "iv-down" : "iv-flat");
const heat = (v, scale) => {
  const step = Math.round(Math.max(-1, Math.min(1, v / scale)) * 5);
  return `iv-h${step < 0 ? "n" : "p"}${Math.abs(step)}`;
};
const longDate = (iso) => {
  const [y, mo, d] = iso.split("-");
  return `${Number(d)} ${MONTHS[Number(mo) - 1]} ${y}`;
};
const chipCls = (on) => (on ? "iv-chip iv-chip--on" : "iv-chip");
const compoundOf = (xs) => (xs.some((x) => x === null) ? null : m.compound(xs));
const held = (xs) => xs.filter((x) => x !== null);

function linePath(values, w, h, lo, hi, log = false) {
  const f = log ? Math.log : (v) => v;
  const span = f(hi) - f(lo) || 1;
  const step = values.length > 1 ? w / (values.length - 1) : 0;
  return values.map((v, i) => `${i ? "L" : "M"}${(i * step).toFixed(1)} ${(h - ((f(v) - f(lo)) / span) * h).toFixed(1)}`).join("");
}

function bandPath(top, bottom, w, h) {
  const step = top.length > 1 ? w / (top.length - 1) : 0;
  const upper = top.map((v, i) => `${i ? "L" : "M"}${(i * step).toFixed(1)} ${(v * h).toFixed(1)}`).join("");
  const lower = bottom.map((v, i) => `L${(i * step).toFixed(1)} ${(v * h).toFixed(1)}`).reverse().join("");
  return upper + lower + "Z";
}

// About how many characters of a sector map label fit in a box this many % wide.
const room = (w, across) => Math.floor((w * across - 14) / 7.7);
const fit = (text, w, across) => {
  const r = room(w, across);
  return text.length <= r ? text : r >= 3 ? text.slice(0, r - 1) + "…" : "";
};

export class Board {
  constructor({ data, switchTemplate, switchSlot, boardTemplate, boardSlot, thinking }) {
    this.D = data;
    this.thinking = thinking;
    this.mounts = [
      [switchTemplate, switchSlot],
      [boardTemplate, boardSlot],
    ];
    this.n = data.returns.length;
    this.bench = Object.fromEntries(data.benchmarks.map((b) => [b.key, b]));
    this.byTicker = Object.fromEntries(data.holdings.map((h) => [h.ticker, h]));
    this.minAt = Math.min(5, this.n);
    this.memo = new Map();
    this.typed = [];
    this.typedAt = 0;
    this.pointAt = null;
    const firstBench = data.benchmarks[0]?.key ?? null;
    this.state = {
      mode: "dash",
      switched: false,
      at: this.n,
      period: this.n >= m.NEED["1y"] ? "1y" : "all",
      bench: firstBench,
      shown: Object.fromEntries(data.benchmarks.map((b) => [b.key, true])),
      logScale: false,
      view: "perf",
      allocBy: "sleeve",
      contribBy: "holding",
      drill: "",
      mcYears: 5,
      mcSeed: 1,
      shock: -0.2,
      chipsShock: -0.1,
      moves: Object.fromEntries(SCENARIOS.map((c) => [c.key, c.move])),
      log: [
        { cls: "iv-log__line iv-log__line--dim", text: "DFIT <GO>  portfolio terminal · end-of-day data" },
        { cls: "iv-log__line", text: "type HELP for the commands, or press 1 to 9" },
      ],
    };
  }

  start() {
    const values = this.values();
    this.views = this.mounts.map(([template, slot]) => mount(template, slot, values));
  }

  setState(patch) {
    this.state = { ...this.state, ...patch };
    if (!this.queued) {
      this.queued = true;
      queueMicrotask(() => {
        this.queued = false;
        const values = this.values();
        this.views.forEach((update) => update(values));
        this.afterRender?.();
        this.afterRender = null;
      });
    }
  }

  cached(key, make) {
    if (!this.memo.has(key)) {
      if (this.memo.size > 40) this.memo.clear();
      this.memo.set(key, make());
    }
    return this.memo.get(key);
  }

  // ---------------------------------------------------------------- commands

  say(lines) {
    this.setState({ log: [...this.state.log, ...lines].slice(-14) });
  }

  run(text) {
    const D = this.D;
    const state = this.state;
    const words = text.trim().split(/\s+/);
    const [command, ...rest] = words.map((w) => w.toLowerCase());
    const arg = rest.join(" ");
    const out = [{ cls: "iv-log__line iv-log__line--cmd", text: "> " + text.trim() }];
    const line = (t, kind = "") => out.push({ cls: "iv-log__line" + (kind ? " iv-log__line--" + kind : ""), text: t });
    const changes = {};
    this.typed.push(text.trim());
    this.typedAt = this.typed.length;
    const viewFor = { perf: "perf", risk: "risk", dd: "risk", alloc: "alloc", hold: "hold", corr: "corr", mc: "mc", stress: "stress", trades: "trades", notes: "notes" };

    if (command === "help") {
      [
        "PERF [1m|3m|ytd|1y|all]   returns against the benchmarks",
        "RISK  ·  DD                 volatility, drawdowns, ratios",
        "ALLOC [sleeve|sector|region|asset|currency]",
        "HOLD [ticker]               holdings, or one in detail",
        "CORR  ·  MC [years]  ·  STRESS [-20]",
        "TRADES  ·  NOTES            trades and weights, the thinking",
        "DEF [term]                  what a figure means, e.g. DEF SHARPE",
        "BENCH [75/25|acwi]  ·  DATE [yyyy-mm-dd|latest]  ·  CLEAR",
        "DASH                        back to the dashboard",
      ].forEach((t) => line(t));
    } else if (command === "clear") {
      this.setState({ log: [] });
      return;
    } else if (command === "dash" || command === "exit") {
      this.setState({ mode: "dash", switched: true });
      return;
    } else if (command === "def" || command === "define") {
      const found = arg && (D.glossary.find((g) => g.term.toLowerCase().startsWith(arg)) || D.glossary.find((g) => g.term.toLowerCase().includes(arg)));
      if (found) line(`${found.term}: ${found.text}`);
      else line(arg ? `nothing called ${arg.toUpperCase()} · NOTES lists every term` : "DEF SHARPE, DEF BETA, DEF DRAWDOWN… · NOTES lists every term", "err");
    } else if (viewFor[command]) {
      changes.view = viewFor[command];
      if (command === "perf" && PERIODS.some((p) => p.key === arg)) {
        if (state.at >= m.NEED[arg]) changes.period = arg;
        else line(`not enough history for ${arg.toUpperCase()} yet`, "err");
      }
      if (command === "alloc" && arg) {
        const by = ALLOC_BY.find((a) => a.key === arg || a.label.toLowerCase().startsWith(arg));
        if (by) changes.allocBy = by.key;
      }
      if (command === "mc" && Number(arg) > 0) changes.mcYears = Math.min(10, Math.max(1, Math.round(Number(arg))));
      if (command === "stress" && arg && Number.isFinite(Number(arg))) changes.shock = Math.max(-50, Math.min(30, Number(arg))) / 100;
      if (command === "hold" && arg) {
        const h = this.byTicker[arg.toUpperCase()];
        if (h) {
          changes.drill = h.sector;
          line(`${h.ticker}  ${h.name} · ${h.sector} · ${h.region} · weight ${pct(h.weights[state.at], 1, false)}`);
        } else {
          line(`no holding called ${arg.toUpperCase()}`, "err");
        }
      }
      line(`→ ${VIEWS.find((v) => v.key === changes.view).label.toUpperCase()}`, "dim");
    } else if (command === "bench") {
      const key = arg === "75/25" || arg === "policy" ? "policy" : arg;
      if (this.bench[key]) {
        changes.bench = key;
        changes.shown = { ...state.shown, [key]: true };
        line("benchmark: " + this.bench[key].name);
      } else {
        line(D.benchmarks.length ? `BENCH ${D.benchmarks.map((b) => b.code).join(" or BENCH ")}` : "no benchmark prices loaded yet", "err");
      }
    } else if (command === "date" || command === "latest") {
      if (command === "latest" || arg === "latest" || !arg) {
        changes.at = this.n;
        line("as of the latest close");
      } else {
        const i = D.dates.findIndex((d) => d >= arg);
        if (i < 0 || !/^\d{4}-\d{2}-\d{2}$/.test(arg)) {
          line("DATE 2026-11-02, or DATE LATEST", "err");
        } else {
          changes.at = Math.max(this.minAt, i);
          line("as of " + longDate(D.dates[changes.at]));
        }
      }
    } else {
      line(`unknown command: ${command.toUpperCase()} · type HELP`, "err");
    }
    this.setState({ ...changes, log: [...state.log, ...out].slice(-14) });
  }

  openTerminal() {
    const state = this.state;
    const period = PERIODS.find((p) => p.key === state.period).label;
    const bench = this.bench[state.bench]?.code;
    const note = `from the dashboard · ${period}${bench ? " vs " + bench : ""} · as of ${longDate(this.D.dates[state.at])}`;
    this.afterRender = () => this.prompt?.focus({ preventScroll: true });
    this.setState({ mode: "term", switched: true, log: [...state.log, { cls: "iv-log__line iv-log__line--dim", text: note }].slice(-14) });
  }

  // ---------------------------------------------------------------- the chart readout

  readout(index) {
    const c = this.chart;
    const el = this.crossChart;
    if (!c || !el) return;
    const svg = el.querySelector(".iv-chart__svg");
    const cross = el.querySelector(".iv-cross");
    const count = c.lines[0].values.length;
    const i = Math.max(0, Math.min(count - 1, index));
    this.pointAt = i;
    const box = svg.getBoundingClientRect();
    const outer = el.getBoundingClientRect();
    const x = box.left - outer.left + (count > 1 ? i / (count - 1) : 0) * box.width;
    const f = c.log ? Math.log : (v) => v;
    cross.hidden = false;
    cross.style.left = `${x}px`;
    cross.style.height = `${box.height}px`;
    cross.classList.toggle("iv-cross--flip", x > outer.width * 0.62);
    const dots = cross.querySelector(".iv-cross__dots");
    const tip = cross.querySelector(".iv-cross__tip");
    dots.replaceChildren();
    tip.replaceChildren();
    const head = document.createElement("b");
    head.textContent = longDate(this.D.dates[c.start + i]);
    tip.append(head);
    for (const l of c.lines) {
      const v = l.values[i];
      const dot = document.createElement("span");
      dot.className = `iv-dot--${l.key}`;
      dot.style.top = `${(1 - (f(v) - f(c.lo)) / (f(c.hi) - f(c.lo))) * box.height}px`;
      dots.append(dot);
      const row = document.createElement("span");
      const key = document.createElement("i");
      key.className = `iv-dot--${l.key}`;
      const name = document.createElement("span");
      name.textContent = l.name;
      const value = document.createElement("span");
      value.textContent = `${v.toFixed(1)}  ${pct(v / 100 - 1)}`;
      row.append(key, name, value);
      tip.append(row);
    }
  }

  // Lights up one sleeve's band and its legend entry, and dims the rest.
  focusBand(el, off = false) {
    const panel = el.closest(".iv-panel");
    const key = el.dataset.band;
    panel?.querySelectorAll("[data-band]").forEach((node) => {
      const mine = node.dataset.band === key;
      node.classList.toggle("is-dim", !off && !mine);
      node.classList.toggle("is-on", !off && mine);
    });
  }

  // Each sleeve's weight on a day, against its target, following the pointer or arrow keys.
  bandsReadout(chart, index) {
    const { stacks, at } = this.bandStacks;
    const i = Math.max(0, Math.min(at, index));
    this.bandAt = i;
    const svg = chart.querySelector(".iv-bands");
    const cross = chart.querySelector(".iv-cross");
    const box = svg.getBoundingClientRect();
    const outer = chart.getBoundingClientRect();
    const x = box.left - outer.left + (at ? i / at : 0) * box.width;
    cross.hidden = false;
    cross.style.left = `${x}px`;
    cross.style.height = `${box.height}px`;
    cross.classList.toggle("iv-cross--flip", x > outer.width * 0.55);
    const tip = cross.querySelector(".iv-cross__tip");
    tip.replaceChildren();
    const head = document.createElement("b");
    head.textContent = longDate(this.D.dates[i]);
    tip.append(head);
    for (const band of [...stacks].reverse()) {
      const row = document.createElement("span");
      const key = document.createElement("i");
      key.className = `iv-dot--${band.key}`;
      const name = document.createElement("span");
      name.textContent = band.name;
      const value = document.createElement("span");
      value.textContent = `${pct(band.share[i], 1, false)} / ${pct(band.target, 0, false)}`;
      row.append(key, name, value);
      tip.append(row);
    }
  }

  hideReadout() {
    const cross = this.crossChart?.querySelector(".iv-cross");
    if (cross) cross.hidden = true;
  }

  // ---------------------------------------------------------------- the figures

  values() {
    const D = this.D;
    const state = this.state;
    const n = this.n;
    const at = state.at;
    const dates = D.dates;
    // A period the history doesn't cover yet falls back to the whole history.
    const period = at >= m.NEED[state.period] ? state.period : "all";
    const start = m.periodStart(dates, period, at);
    const periodLabel = PERIODS.find((p) => p.key === period).label;
    const win = (xs) => xs.slice(start, at);
    const r = win(D.returns);
    const rf = win(D.riskFree);
    const benchKey = this.bench[state.bench] ? state.bench : null;
    const b = benchKey ? win(this.bench[benchKey].returns) : null;
    const S = this.cached(`s${at}${period}${benchKey}`, () => m.stats(r, rf, b));
    const whole = this.cached(`w${at}${benchKey}`, () =>
      m.stats(D.returns.slice(0, at), D.riskFree.slice(0, at), benchKey ? this.bench[benchKey].returns.slice(0, at) : null),
    );
    const ratios = at >= m.NEED_RATIOS;
    const benchCode = benchKey ? this.bench[benchKey].code : null;
    const holdings = D.holdings.filter((h) => h.weights[at] > 0);
    const weightOf = (h) => h.weights[at];
    const cash = D.cash[at];
    const latest = at === n;

    // The status line, or where the time machine is.
    let statusCls = "iv-status";
    let statusText = D.status.text;
    if (!latest) {
      statusText = `Time machine: everything shows the portfolio as it was at the close of ${longDate(dates[at])}.`;
    } else if (D.status.late) {
      statusCls += " iv-status--late";
    }

    // ------------------------------------------------ growth of 100
    const W = 1000;
    const lines = [{ key: "port", name: "Portfolio", values: m.growth(r) }];
    for (const bm of D.benchmarks) {
      if (state.shown[bm.key]) lines.push({ key: bm.key, name: bm.code, values: m.growth(win(bm.returns)) });
    }
    const flat = lines.flatMap((l) => l.values);
    let lo = Math.min(...flat);
    let hi = Math.max(...flat);
    const pad = (hi - lo) * 0.08 || 1;
    lo -= pad;
    hi += pad;
    const growthLines = lines.map((l) => ({
      key: l.key,
      d: linePath(l.values, W, 300, lo, hi, state.logScale),
      label: `${l.name} ${pct(l.values[l.values.length - 1] / 100 - 1)}`,
    }));
    this.chart = { lines, lo, hi, start, log: state.logScale };
    const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) =>
      (state.logScale ? Math.exp(Math.log(lo) + (Math.log(hi) - Math.log(lo)) * f) : lo + (hi - lo) * f).toFixed(0),
    );

    // ------------------------------------------------ returns over each period
    const rows = [{ key: "port", label: "Portfolio", series: D.returns }];
    for (const bm of D.benchmarks) rows.push({ key: bm.key, label: `${bm.code} · ${bm.name}`, series: bm.returns });
    if (D.chips) {
      const pad = Array(D.chips.start).fill(null);
      rows.push({ key: "chips", label: "Chip holdings", series: [...pad, ...D.chips.sleeve] });
      rows.push({ key: "semi", label: "SEMI · the chip fund", series: [...pad, ...D.chips.fund] });
    }
    const returnsTable = rows.map((row) => ({
      key: row.key,
      label: row.label,
      cells: PERIODS.map((p) => {
        const value = at >= m.NEED[p.key] ? compoundOf(row.series.slice(m.periodStart(dates, p.key, at), at)) : null;
        return { text: pct(value), cls: tone(value) };
      }),
    }));

    // ------------------------------------------------ drawdowns and months
    const falls = m.drawdowns(r);
    const floor = Math.min(-0.01, falls.worst * 1.1);
    const step = W / Math.max(1, falls.series.length - 1);
    const ddPath = `M0 0${falls.series.map((v, i) => `L${(i * step).toFixed(1)} ${((v / floor) * 120).toFixed(1)}`).join("")}L${W} 0Z`;
    const months = m.monthly(dates.slice(1, at + 1), D.returns.slice(0, at));
    const byYear = {};
    for (const mo of months) (byYear[mo.key.slice(0, 4)] ??= {})[Number(mo.key.slice(5))] = mo.value;
    const years = Object.keys(byYear).sort().map((year) => {
      let total = 1;
      const cells = MONTHS.map((_, k) => {
        const v = byYear[year][k + 1];
        if (v === undefined) return { text: "", cls: "iv-heat__cell--empty" };
        total *= 1 + v;
        return { text: (v * 100).toFixed(1), cls: heat(v, 0.08) };
      });
      return { year, cells, total: pct(total - 1), cls: tone(total - 1) };
    });
    const best = months.reduce((x, y) => (y.value > x.value ? y : x), months[0]);
    const worst = months.reduce((x, y) => (y.value < x.value ? y : x), months[0]);
    const monthName = (mo) => (mo ? `${MONTHS[Number(mo.key.slice(5)) - 1]} ${mo.key.slice(0, 4)} ${pct(mo.value)}` : DASH);

    // ------------------------------------------------ where the return came from
    const parts = Object.fromEntries(D.holdings.map((h) => [h.ticker, win(h.contributions)]));
    const linked = m.contributions(parts, r);
    let contrib = D.holdings.map((h) => ({ name: h.ticker, sector: h.sector, value: linked.totals[h.ticker] })).filter((x) => Math.abs(x.value) > 1e-9 || this.byTicker[x.name].weights[at] > 0);
    if (state.contribBy === "sector") {
      const g = {};
      for (const x of contrib) g[x.sector] = (g[x.sector] || 0) + x.value;
      contrib = Object.entries(g).map(([name, value]) => ({ name, value }));
    }
    contrib.sort((x, y) => y.value - x.value);
    contrib.push({ name: "Cash and costs", value: linked.other });
    const widest = Math.max(...contrib.map((x) => Math.abs(x.value)), 1e-4);
    const contribRows = contrib.map((x) => {
      const w = (Math.abs(x.value) / widest) * 50;
      const shown = Number((x.value * 100).toFixed(2)) + 0;
      return {
        name: x.name,
        text: `${shown > 0 ? "+" : shown === 0 ? "+" : ""}${shown.toFixed(2)} pts`,
        cls: tone(x.value),
        fill: x.value >= 0 ? "iv-fill--up" : "iv-fill--down",
        x: `${(x.value >= 0 ? 50 : 50 - w).toFixed(2)}%`,
        w: `${w.toFixed(2)}%`,
      };
    });

    // ------------------------------------------------ holdings, risk and correlation
    const varP = m.sd(r) ** 2 || 1;
    const stat = (h) =>
      this.cached(`h${h.ticker}${at}${period}${benchKey}`, () => {
        const mine = win(h.returns);
        const [x, y] = m.paired(mine, r);
        const [bx, by] = b ? m.paired(mine, b) : [[], []];
        const s = m.periodStart(dates, "1m", at);
        const ytd = m.periodStart(dates, "ytd", at);
        const ret = (from) => {
          const xs = held(h.returns.slice(from, at));
          return xs.length ? m.compound(xs) : null;
        };
        return {
          ret: ret(start),
          day: at ? h.returns[at - 1] : null,
          month: ret(s),
          ytd: ret(ytd),
          beta: bx.length > 1 ? m.beta(bx, by) : null,
          vol: held(mine).length > 1 ? m.sd(held(mine)) * Math.sqrt(m.TRADING_DAYS) : null,
          risk: (h.weights[at] * m.cov(x, y)) / varP,
        };
      });
    const drill = state.drill;
    const biggest = Math.max(...holdings.map(weightOf), 1e-4);
    const holdingsRows = holdings
      .filter((h) => !drill || h.sector === drill)
      .sort((x, y) => weightOf(y) - weightOf(x))
      .map((h) => {
        const s = stat(h);
        return {
          ticker: h.ticker,
          name: h.name,
          sector: h.sector,
          weight: pct(weightOf(h), 1, false),
          bar: `${((weightOf(h) / biggest) * 100).toFixed(1)}%`,
          cells: [
            { text: pct(s.day, 2), cls: tone(s.day) },
            { text: pct(s.month), cls: tone(s.month) },
            { text: pct(s.ytd), cls: tone(s.ytd) },
            { text: pct(s.ret), cls: tone(s.ret) },
          ],
          beta: num(s.beta),
          vol: pct(s.vol, 0, false),
          risk: pct(s.risk, 1, false),
          pick: () => this.setState({ drill: drill === h.sector ? "" : h.sector }),
        };
      });
    const top = [...holdings].sort((x, y) => stat(y).risk - stat(x).risk).slice(0, 10);
    const riskScale = Math.max(...top.map((h) => Math.max(stat(h).risk, weightOf(h))), 1e-4);
    const riskBars = top.map((h) => ({
      ticker: h.ticker,
      weight: pct(weightOf(h), 1, false),
      risk: pct(stat(h).risk, 1, false),
      w: `${((weightOf(h) / riskScale) * 100).toFixed(1)}%`,
      r: `${((Math.max(0, stat(h).risk) / riskScale) * 100).toFixed(1)}%`,
    }));
    const sleeveOrder = D.sleeves.map((s) => s.key);
    const corrOrder = [...holdings].sort((x, y) => sleeveOrder.indexOf(x.sleeve) - sleeveOrder.indexOf(y.sleeve) || weightOf(y) - weightOf(x));
    const corrRows = this.cached(`c${at}${period}`, () =>
      corrOrder.map((h) => ({
        ticker: h.ticker,
        cells: corrOrder.map((g) => {
          let v = 1;
          if (g !== h) {
            const [x, y] = m.paired(win(h.returns), win(g.returns));
            v = m.correlation(x, y);
          }
          const shown = Number(v.toFixed(2)) + 0;
          return { text: shown === 1 ? "1" : shown.toFixed(2).replace("0.", "."), cls: heat(v, 1) };
        }),
      })),
    );

    // ------------------------------------------------ the sector map and allocation
    const group = (field) => {
      const g = {};
      for (const h of holdings) {
        const key = field === "currency" ? h.currency : h[field];
        g[key] ??= { key, weight: 0, made: 0 };
        g[key].weight += weightOf(h);
        g[key].made += weightOf(h) * (stat(h).ret ?? 0);
      }
      return Object.values(g).map((x) => ({ ...x, ret: x.weight ? x.made / x.weight : 0 }));
    };
    const sectors = group("sector");
    if (cash > 0.0005) sectors.push({ key: "Cash", weight: cash, ret: 0 });
    sectors.sort((x, y) => y.weight - x.weight);
    const inSector = drill ? holdings.filter((h) => h.sector === drill).sort((x, y) => weightOf(y) - weightOf(x)) : [];
    const boxes = drill
      ? m.treemap(inSector.map((h) => ({ name: h.ticker, sub: h.name, weight: weightOf(h), ret: stat(h).ret ?? 0 })))
      : m.treemap(sectors.map((x) => ({ name: x.key, weight: x.weight, ret: x.ret })));
    const drillTotal = m.sum(inSector.map(weightOf)) || 1;
    // A box this % wide is about this many pixels across.
    const across = this.treeWidth || 6;
    const treeBoxes = boxes.map((x) => {
      const share = drill ? x.weight / drillTotal : x.weight;
      const meta = `${pct(share, 1, false)} · ${pct(x.ret)}`;
      return {
        name: fit(x.name, x.w, across),
        full: `${x.sub ? x.sub : x.name}: ${meta}`,
        meta: room(x.w, across) >= meta.length ? meta : pct(share, 1, false),
        small: x.h < 14 || room(x.w, across) < 5,
        cls: heat(x.ret, 0.3),
        x: `${x.x}%`,
        y: `${x.y}%`,
        w: `${x.w}%`,
        h: `${x.h}%`,
        pick: () => {
          if (drill) this.setState({ drill: "" });
          else if (x.name !== "Cash") this.setState({ drill: x.name });
        },
      };
    });

    const allocBy = state.allocBy;
    const sleeveName = Object.fromEntries(D.sleeves.map((s) => [s.key, s.name]));
    let allocRows;
    if (allocBy === "sleeve") {
      const g = Object.fromEntries(group("sleeve").map((x) => [x.key, x]));
      allocRows = D.sleeves.map((s) => {
        const weight = s.key === "cash" ? cash : g[s.key]?.weight ?? 0;
        const ret = s.key === "cash" ? null : g[s.key]?.ret ?? null;
        const target = D.targets[s.key] ?? 0;
        return { name: s.name, weight, ret, target };
      });
    } else {
      const field = { sector: "sector", region: "region", asset: "asset", currency: "currency" }[allocBy];
      allocRows = group(field).map((x) => ({ name: x.key, weight: x.weight, ret: x.ret, target: null }));
      allocRows.push({ name: "Cash", weight: cash, ret: null, target: null });
      allocRows.sort((x, y) => y.weight - x.weight);
    }
    const allocScale = allocBy === "sleeve" ? 0.4 : Math.max(...allocRows.map((x) => x.weight), 0.01);
    const shares = m.sum(holdings.filter((h) => h.asset === "Shares").map(weightOf));
    const bonds = m.sum(holdings.filter((h) => h.asset === "Bonds").map(weightOf));
    const gold = m.sum(holdings.filter((h) => h.asset === "Gold").map(weightOf));
    const allWeights = [...holdings.map(weightOf), cash];

    // ------------------------------------------------ weights over time and trades
    const bands = [];
    const stacks = [];
    let below = Array(at + 1).fill(0);
    for (const s of D.sleeves) {
      const share = below.map((_, t) => (s.key === "cash" ? D.cash[t] : m.sum(D.holdings.filter((h) => h.sleeve === s.key).map((h) => h.weights[t]))));
      const above = below.map((v, t) => v + share[t]);
      stacks.push({ key: s.key, name: s.name, share, target: D.targets[s.key] ?? 0 });
      bands.push({
        key: s.key,
        name: s.name,
        now: pct(share[at], 1, false),
        target: pct(D.targets[s.key] ?? 0, 0, false),
        d: bandPath(above.map((v) => 1 - v), below.map((v) => 1 - v), W, 200),
      });
      below = above;
    }
    this.bandStacks = { stacks, at };
    const done = D.trades.filter((t) => t.day <= at);
    const tradeRows = done
      .slice()
      .reverse()
      .slice(0, 8)
      .map((t) => {
        const h = this.byTicker[t.ticker];
        const before = t.day ? h.weights[t.day - 1] : 0;
        const after = h.weights[t.day];
        const verb = before === 0 ? "Bought" : after === 0 ? "Sold" : after > before ? "Added to" : "Trimmed";
        return {
          date: longDate(dates[t.day]),
          verb,
          cls: after >= before ? "iv-trade--buy" : "iv-trade--sell",
          ticker: t.ticker,
          name: h.name,
          change: `${pct(before, 1, false)} → ${pct(after, 1, false)}`,
        };
      });
    const later = D.turnover.filter((t) => t.day <= at && t.day > at - 252);
    const turned = m.sum(later.map((t) => t.weight)) / 2;

    // ------------------------------------------------ the factsheet
    const facts = [
      ["Return, annualised", S.cagr === null ? pct(S.annual) + "*" : pct(S.cagr), true],
      ["Volatility", pct(S.vol, 1, false)],
      ["Sharpe ratio", num(S.sharpe), true],
      ["Sortino ratio", num(S.sortino), true],
      ["Calmar ratio", num(S.calmar), true],
      ["Max drawdown", pct(S.maxDD)],
      ["Recovery", S.recoveryDays === null ? "not yet" : `${S.recoveryDays} days`],
      ["Current drawdown", pct(S.currentDD)],
      ["Beta", num(S.beta)],
      ["Alpha, annualised", pct(S.alpha), true],
      ["Correlation", num(S.corr)],
      ["Tracking error", pct(S.te, 1, false)],
      ["Information ratio", num(S.ir), true],
      ["Up capture", pct(S.upCapture, 0, false), true],
      ["Down capture", pct(S.downCapture, 0, false), true],
      ["VaR 95%, 1 day", pct(-S.var95, 2)],
      ["Expected shortfall 95%", pct(-S.cvar95, 2)],
      ["Best day", pct(S.best, 2)],
      ["Worst day", pct(S.worst, 2)],
      ["Positive days", pct(S.hitRate, 0, false)],
      ["Skew", num(S.skew), true],
      ["Excess kurtosis", num(S.kurt), true],
    ].map(([label, value, short]) => ({ label, value: short && !ratios ? DASH : value }));

    // ------------------------------------------------ rolling, daily returns
    const wait = (need, what) => ({ text: `${what} Day ${at} of ${need}.`, bar: `${Math.min(100, (at / need) * 100).toFixed(0)}%` });
    let rolling = null;
    let rollingWait = null;
    if (at < m.NEED_ROLLING || !benchKey) {
      rollingWait = wait(m.NEED_ROLLING, at < m.NEED_ROLLING ? "This needs four months of history: a three-month window, and a month of it moving." : "This needs the benchmark's prices, which aren't in yet.");
    } else {
      const points = this.cached(`r${at}${benchKey}`, () => {
        const out = [];
        const span = 63;
        const all = D.returns.slice(0, at);
        const bench = this.bench[benchKey].returns.slice(0, at);
        for (let i = span; i <= all.length; i += 3) {
          const w = all.slice(i - span, i);
          out.push([m.sd(w) * Math.sqrt(m.TRADING_DAYS), m.beta(w, bench.slice(i - span, i))]);
        }
        return out;
      });
      const vols = points.map((p) => p[0]);
      const betas = points.map((p) => p[1]);
      rolling = {
        vol: linePath(vols, W, 120, 0, Math.max(...vols) * 1.1),
        beta: linePath(betas, W, 120, 0, Math.max(2, ...betas)),
        volNow: pct(vols[vols.length - 1], 1, false),
        betaNow: num(betas[betas.length - 1]),
      };
    }
    const binW = 0.005;
    const edge = 0.06;
    const count = Math.round((2 * edge) / binW);
    const bins = Array(count).fill(0);
    for (const v of r) bins[Math.min(count - 1, Math.max(0, Math.floor((v + edge) / binW)))] += 1;
    const mu = m.mean(r);
    const spread = m.sd(r) || 0.01;
    const peak = (binW * r.length) / (spread * Math.sqrt(2 * Math.PI));
    const topBin = Math.max(...bins, peak, 1);
    const slot = W / count;
    const histBars = bins
      .map((c, i) => ({ c, i }))
      .filter(({ c }) => c)
      .map(({ c, i }) => ({
        x: (i * slot + 1).toFixed(1),
        w: (slot - 2).toFixed(1),
        y: (120 - (c / topBin) * 120).toFixed(1),
        h: ((c / topBin) * 120).toFixed(1),
        cls: -edge + i * binW < 0 ? "iv-bin--down" : "",
      }));
    const histCurve = bins
      .map((_, i) => {
        const centre = -edge + (i + 0.5) * binW;
        const y = peak * Math.exp(-(((centre - mu) / spread) ** 2) / 2);
        return `${i ? "L" : "M"}${((i + 0.5) * slot).toFixed(1)} ${(120 - (y / topBin) * 120).toFixed(1)}`;
      })
      .join("");

    // ------------------------------------------------ Monte Carlo
    const horizon = state.mcYears;
    let mc = null;
    let mcWait = null;
    if (at < m.NEED_MC) {
      mcWait = wait(m.NEED_MC, "This needs six months of history. A projection built from less would only replay one kind of market.");
    } else {
      const p = this.cached(`mc${at}${horizon}${state.mcSeed}`, () => m.monteCarlo(D.returns.slice(0, at), horizon, state.mcSeed));
      const mcHi = Math.max(p.bands[p.bands.length - 1][4], 1.2) * 1.05;
      const mcLo = Math.min(...p.bands.map((x) => x[0]), 0.9) * 0.95;
      const y = (v) => (300 - ((Math.log(v) - Math.log(mcLo)) / (Math.log(mcHi) - Math.log(mcLo))) * 300).toFixed(1);
      const stepX = W / (p.bands.length - 1);
      const band = (low, high) =>
        p.bands.map((x, i) => `${i ? "L" : "M"}${(i * stepX).toFixed(1)} ${y(x[high])}`).join("") +
        p.bands.map((x, i) => `L${(i * stepX).toFixed(1)} ${y(x[low])}`).reverse().join("") +
        "Z";
      const final = p.bands[p.bands.length - 1];
      const outcome = (v) => `${pct(v - 1, 0)} · ${pct(v ** (1 / horizon) - 1)} a year`;
      mc = {
        outer: band(0, 4),
        inner: band(1, 3),
        median: linePath(p.bands.map((x) => x[2]), W, 300, mcLo, mcHi, true),
        samples: p.samples.map((s) => linePath(s, W, 300, mcLo, mcHi, true)),
        medianText: outcome(final[2]),
        lowText: outcome(final[0]),
        highText: outcome(final[4]),
        lossText: pct(p.loss, 0, false),
      };
    }

    // ------------------------------------------------ stress
    const scenarios = SCENARIOS.map((c) => {
      const move = state.moves[c.key];
      const hit = holdings.filter((h) => c.picks(h));
      const total = m.sum(hit.map((h) => weightOf(h) * move));
      return {
        key: c.key,
        label: c.label,
        move: pct(move, 0),
        moveCls: tone(move),
        value: String(Math.round(move * 100)),
        min: String(c.min),
        max: String(c.max),
        onMove: (e) => this.setState({ moves: { ...this.state.moves, [c.key]: Number(e.target.value) / 100 } }),
        total: pct(total, 2),
        cls: tone(total),
        holdings: hit.sort((x, y) => weightOf(y) - weightOf(x)).map((h) => h.ticker).join(", ") || DASH,
      };
    });
    const scenariosChanged = SCENARIOS.some((c) => Math.abs(state.moves[c.key] - c.move) > 1e-9);
    let sliders = null;
    let slidersWait = null;
    const fund = this.byTicker[CHIPS_FUND];
    if (!this.bench.acwi) {
      slidersWait = "The sliders, which move world shares and chips and estimate what each holding would do, need the world shares prices, which aren't in yet.";
    } else if (at < m.NEED_RATIOS) {
      slidersWait = `The sliders, which move world shares and chips and estimate what each holding would do, need three months of history to measure each holding's sensitivity. Day ${at} of ${m.NEED_RATIOS}.`;
    } else if (fund) {
      const look = Math.max(0, at - 252);
      const sens = this.cached(`st${at}`, () => {
        const market = this.bench.acwi.returns.slice(look, at);
        const chipDays = fund.returns.slice(look, at);
        const ok = chipDays.map((x) => x !== null);
        const pick = (xs) => xs.filter((_, i) => ok[i]);
        return m.sensitivities(Object.fromEntries(holdings.map((h) => [h.ticker, pick(h.returns.slice(look, at))])), pick(market), pick(chipDays));
      });
      const moves = holdings.map((h) => ({ h, move: sens[h.ticker].market * state.shock + sens[h.ticker].chips * state.chipsShock }));
      const total = m.sum(moves.map((x) => weightOf(x.h) * x.move));
      sliders = {
        total: pct(total),
        cls: tone(total),
        rows: moves
          .sort((x, y) => weightOf(x.h) * x.move - weightOf(y.h) * y.move)
          .map((x) => ({
            ticker: x.h.ticker,
            move: pct(x.move),
            cls: tone(x.move),
            fill: x.move < 0 ? "iv-fill--down" : "iv-fill--up",
            bar: `${Math.min(100, (Math.abs(x.move) * 100) / 0.8).toFixed(1)}%`,
            contrib: pct(weightOf(x.h) * x.move, 2),
          })),
      };
    }

    // ------------------------------------------------ the terminal's strip and tape
    const metrics = [
      ["Return", pct(S.total), tone(S.total)],
      [benchCode || "Benchmark", pct(S.benchTotal), tone(S.benchTotal)],
      ["Volatility", pct(S.vol, 1, false), "iv-flat"],
      ["Sharpe", ratios ? num(S.sharpe) : DASH, "iv-flat"],
      ["Max drawdown", pct(S.maxDD), "iv-down"],
      ["Beta", num(S.beta), "iv-flat"],
    ].map(([label, value, cls]) => ({ label, value, cls }));
    const tape = [...holdings]
      .sort((x, y) => weightOf(y) - weightOf(x))
      .map((h) => {
        const day = at ? h.returns[at - 1] : null;
        return { ticker: h.ticker, weight: pct(weightOf(h), 1, false), day: day === null ? DASH : (day >= 0 ? "▲" : "▼") + Math.abs(day * 100).toFixed(2) + "%", cls: tone(day) };
      });

    const term = state.mode === "term";
    const view = state.view;
    const go = (key) => this.setState({ view: key });
    const byKey = (e) => {
      const fn = /^F([1-9])$/.exec(e.key);
      const digit = /^[1-9]$/.exec(e.key);
      return fn ? VIEWS[Number(fn[1]) - 1] : digit ? VIEWS[Number(e.key) - 1] : null;
    };

    return {
      // the switch
      switchCls: term ? "iv-switch iv-switch--term" : "iv-switch",
      dashPressed: String(!term),
      termPressed: String(term),
      switchHint: term ? "1 to 9 change the view · / for the command line · Esc to leave" : "the same figures, as a trading terminal",
      openDashboard: () => this.setState({ mode: "dash", switched: true }),
      openTerminal: () => this.openTerminal(),
      modeDash: !term,
      modeTerm: term,
      dashCls: state.switched ? "iv-dash iv-view iv-view--in" : "iv-dash",
      statusCls,
      statusText,

      // the time machine
      at: String(at),
      atMin: String(this.minAt),
      atMax: String(n),
      onScrub: (e) => this.setState({ at: Math.max(this.minAt, Number(e.target.value)) }),
      latest: () => this.setState({ at: n }),
      notLatest: !latest,
      scrubLabel: latest ? "latest" : "as of " + longDate(dates[at]),
      scrubFrom: longDate(dates[this.minAt]),
      scrubTo: longDate(dates[n]),

      inception: longDate(dates[0]),
      asOf: longDate(dates[at]),
      days: String(at),
      periodLabel,
      benchCode,
      vsBench: benchCode ? ` vs ${benchCode}` : "",
      noBenchmarks: !D.benchmarks.length,
      tiles: [
        { label: "Return", value: pct(whole.total), cls: tone(whole.total), note: whole.cagr === null ? `in ${at} trading days` : `${pct(whole.cagr)} a year` },
        { label: "Volatility", value: pct(whole.vol, 1, false), cls: "", note: ratios ? "annualised" : "annualised, early days" },
        { label: "Sharpe ratio", value: ratios ? num(whole.sharpe) : DASH, cls: "", note: ratios ? `risk-free ${D.riskFreeSource}` : `after 3 months · day ${at} of ${m.NEED_RATIOS}` },
        { label: "Worst fall", value: pct(whole.maxDD), cls: "iv-down", note: "from a peak" },
        { label: "Beta", value: num(whole.beta), cls: "", note: benchCode ? `to the ${benchCode} benchmark` : "once benchmark prices are in" },
        { label: "Holdings", value: String(holdings.length), cls: "", note: `${pct(cash, 1, false)} cash` },
      ],
      sinceInception: pct(whole.total),
      sinceCls: tone(whole.total),
      cashWeight: pct(cash, 1, false),
      showCash: !drill,

      periods: PERIODS.map((p) => {
        const ready = at >= m.NEED[p.key];
        return {
          label: p.label,
          cls: ready ? chipCls(p.key === period) : "iv-chip iv-chip--off",
          pressed: String(p.key === period),
          disabled: String(!ready),
          pick: () => ready && this.setState({ period: p.key }),
        };
      }),
      periodHeads: PERIODS.map((p) => p.label),
      benches: D.benchmarks.map((bm) => ({
        key: bm.key,
        code: bm.code,
        name: bm.name,
        cls: state.shown[bm.key] ? "iv-toggle iv-toggle--on" : "iv-toggle",
        pressed: String(Boolean(state.shown[bm.key])),
        pick: () => this.setState({ shown: { ...state.shown, [bm.key]: !state.shown[bm.key] } }),
      })),
      benchChoices: D.benchmarks.map((bm) => ({
        code: bm.code,
        name: bm.name,
        cls: chipCls(bm.key === benchKey),
        pressed: String(bm.key === benchKey),
        pick: () => this.setState({ bench: bm.key }),
      })),
      logLabel: state.logScale ? "log" : "linear",
      logPressed: String(state.logScale),
      toggleLog: () => this.setState({ logScale: !state.logScale }),

      growthLines,
      portArea: `${growthLines[0].d}L${W} 300L0 300Z`,
      ticks,
      xLabels: [start, Math.round((start + at) / 2), at].map((i) => longDate(dates[i])),
      crossRef: (el) => {
        if (el) this.crossChart = el.parentElement;
      },
      onChartMove: (e) => {
        const svg = e.currentTarget.querySelector(".iv-chart__svg");
        const box = svg.getBoundingClientRect();
        const count = this.chart.lines[0].values.length;
        this.crossChart = e.currentTarget;
        this.readout(Math.round(((e.clientX - box.left) / box.width) * (count - 1)));
      },
      onChartLeave: () => this.hideReadout(),
      onChartKey: (e) => {
        const count = this.chart.lines[0].values.length;
        const jump = e.shiftKey ? 10 : 1;
        const moves = { ArrowLeft: -jump, ArrowRight: jump };
        this.crossChart = e.currentTarget;
        if (e.key in moves) {
          e.preventDefault();
          e.stopPropagation();
          this.readout((this.pointAt ?? count - 1) + moves[e.key]);
        } else if (e.key === "Home" || e.key === "End") {
          e.preventDefault();
          this.readout(e.key === "Home" ? 0 : count - 1);
        } else if (e.key === "Escape") {
          this.hideReadout();
        }
      },

      returnsTable,
      ddPath,
      ddWorst: pct(falls.worst),
      ddNow: pct(falls.current),
      monthNames: MONTHS,
      years,
      monthsUp: `${months.filter((x) => x.value > 0).length} of ${months.length}`,
      bestMonth: monthName(best),
      worstMonth: monthName(worst),

      contribBy: ["holding", "sector"].map((k) => ({
        label: k === "holding" ? "Holding" : "Sector",
        cls: chipCls(k === state.contribBy),
        pressed: String(k === state.contribBy),
        pick: () => this.setState({ contribBy: k }),
      })),
      contribRows,
      contribTotal: pct(linked.total, 2),
      riskBars,

      treeBoxes,
      drilled: Boolean(drill),
      drillName: drill,
      undrill: () => this.setState({ drill: "" }),
      treeTitle: drill ? `${drill} · holdings` : "Sectors",
      treeHint: drill ? "click a box to go back" : "click a box to drill in",
      // The map's labels are cut to fit its boxes, so it is measured, and drawn again if its
      // width changes much.
      treeRef: (el) => {
        this.treeObserver?.disconnect();
        if (!el) return;
        this.treeObserver = new ResizeObserver(([entry]) => {
          const across = entry.contentRect.width / 100;
          if (across && Math.abs(across - (this.treeWidth || 0)) > 0.3) {
            this.treeWidth = across;
            this.setState({});
          }
        });
        this.treeObserver.observe(el);
      },
      allocBy: ALLOC_BY.map((a) => ({ label: a.label, cls: chipCls(a.key === allocBy), pressed: String(a.key === allocBy), pick: () => this.setState({ allocBy: a.key }) })),
      allocLabel: ALLOC_BY.find((a) => a.key === allocBy).label.toLowerCase(),
      allocTargets: allocBy === "sleeve",
      allocRows: allocRows.map((x) => ({
        name: allocBy === "sleeve" ? x.name : sleeveName[x.name] || x.name,
        weight: pct(x.weight, 1, false),
        target: x.target === null ? "" : `/ ${pct(x.target, 0, false)}`,
        bar: `${Math.min(100, (x.weight / allocScale) * 100).toFixed(1)}%`,
        mark: `${Math.min(100, ((x.target ?? 0) / allocScale) * 100).toFixed(1)}%`,
        noTarget: x.target === null,
        ret: pct(x.ret),
        cls: tone(x.ret),
      })),
      assetMix: `${pct(shares, 0, false)} shares · ${pct(bonds, 0, false)} bonds · ${pct(gold, 0, false)} gold · ${pct(cash, 0, false)} cash`,
      top5: pct(m.sum([...holdings.map(weightOf)].sort((x, y) => y - x).slice(0, 5)), 0, false),
      effective: m.effectiveHoldings(allWeights).toFixed(1),

      bands,
      bandsFrom: longDate(dates[0]),
      bandsTo: longDate(dates[at]),
      onBandFocus: (e) => this.focusBand(e.currentTarget),
      onBandBlur: (e) => this.focusBand(e.currentTarget, true),
      onBandsMove: (e) => {
        const svg = e.currentTarget.querySelector(".iv-bands");
        const box = svg.getBoundingClientRect();
        this.bandsReadout(e.currentTarget, Math.round(((e.clientX - box.left) / box.width) * this.bandStacks.at));
      },
      onBandsLeave: (e) => {
        const cross = e.currentTarget.querySelector(".iv-cross");
        if (cross) cross.hidden = true;
      },
      onBandsKey: (e) => {
        const jump = e.shiftKey ? 10 : 1;
        const moves = { ArrowLeft: -jump, ArrowRight: jump };
        if (e.key in moves) {
          e.preventDefault();
          e.stopPropagation();
          this.bandsReadout(e.currentTarget, (this.bandAt ?? this.bandStacks.at) + moves[e.key]);
        } else if (e.key === "Escape") {
          e.currentTarget.querySelector(".iv-cross").hidden = true;
        }
      },
      tradeRows,
      tradeCount: `${done.length} trade${done.length === 1 ? "" : "s"}`,
      turnover: later.length ? `${pct(turned, 0, false)} of the portfolio traded in the last year` : "no trades since the first purchases",

      holdingsRows,
      facts,
      ratiosWait: !ratios,
      rolling,
      rollingWait,
      histBars,
      histCurve,
      var95: pct(-S.var95, 2),
      corrTickers: corrOrder.map((h) => h.ticker),
      corrRows,

      mc,
      mcWait,
      mcYears: String(horizon),
      mcYearsLabel: `${horizon} year${horizon === 1 ? "" : "s"}`,
      onYears: (e) => this.setState({ mcYears: Number(e.target.value) }),
      rerun: () => this.setState({ mcSeed: state.mcSeed + 1 }),

      scenarios,
      scenariosChanged,
      resetScenarios: () => this.setState({ moves: Object.fromEntries(SCENARIOS.map((c) => [c.key, c.move])) }),
      presets: PRESETS.map((x) => ({ label: x.label, pick: () => this.setState({ shock: x.shock, chipsShock: x.chips }) })),
      sliders,
      slidersWait,
      shock: String(Math.round(state.shock * 100)),
      shockLabel: pct(state.shock, 0),
      onShock: (e) => this.setState({ shock: Number(e.target.value) / 100 }),
      chipsShock: String(Math.round(state.chipsShock * 100)),
      chipsLabel: pct(state.chipsShock, 0),
      onChips: (e) => this.setState({ chipsShock: Number(e.target.value) / 100 }),

      glossary: D.glossary,
      glossHint: term ? " · or type DEF and a term" : "",
      thinkingRef: (el) => {
        if (el && this.thinking) el.replaceChildren(...[...this.thinking.childNodes].map((node) => node.cloneNode(true)));
      },

      // the terminal
      lampCls: !latest ? "iv-lamp iv-lamp--past" : D.status.late ? "iv-lamp iv-lamp--late" : "iv-lamp",
      lampText: (!latest ? "TIME MACHINE · " : D.status.late ? "STALE · LAST EOD " : "EOD ") + longDate(dates[at]).toUpperCase(),
      metrics,
      tape,
      views: VIEWS.map((v) => ({ fn: v.fn, label: v.label, cls: v.key === view ? "iv-fkey iv-fkey--on" : "iv-fkey", pressed: String(v.key === view), pick: () => go(v.key) })),
      viewPerf: view === "perf",
      viewRisk: view === "risk",
      viewAlloc: view === "alloc",
      viewHold: view === "hold",
      viewCorr: view === "corr",
      viewMc: view === "mc",
      viewStress: view === "stress",
      viewTrades: view === "trades",
      viewNotes: view === "notes",
      log: state.log,
      termRef: (el) => {
        this.term = el;
      },
      promptRef: (el) => {
        this.prompt = el;
      },
      // In the command line: Enter runs it, the arrows recall earlier commands, and a number or
      // an F-key changes the view while nothing has been typed. Esc clears it, then leaves.
      onKey: (e) => {
        const input = e.target;
        const target = byKey(e);
        if (target && (e.key.length > 1 || !input.value)) {
          e.preventDefault();
          go(target.key);
        } else if (e.key === "Enter" && input.value.trim()) {
          const text = input.value;
          input.value = "";
          this.run(text);
        } else if (e.key === "ArrowUp" || e.key === "ArrowDown") {
          e.preventDefault();
          this.typedAt = Math.max(0, Math.min(this.typed.length, this.typedAt + (e.key === "ArrowUp" ? -1 : 1)));
          input.value = this.typed[this.typedAt] || "";
        } else if (e.key === "Escape") {
          if (input.value) input.value = "";
          else this.setState({ mode: "dash", switched: true });
        }
        e.stopPropagation();
      },
      // Anywhere else in the terminal: numbers and F-keys change the view, / goes to the command
      // line, and Esc goes back to the dashboard.
      onPageKey: (e) => {
        const tag = e.target.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA") return;
        const target = byKey(e);
        if (target) {
          e.preventDefault();
          go(target.key);
        } else if (e.key === "/") {
          e.preventDefault();
          this.prompt?.focus();
        } else if (e.key === "Escape") {
          this.setState({ mode: "dash", switched: true });
        }
      },
    };
  }
}
