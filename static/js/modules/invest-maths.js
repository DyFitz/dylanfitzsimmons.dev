// The portfolio maths for the investments page. The same formulas as the server's
// (apps/investments/analytics.py), so the figures the page arrives with and the ones worked
// out here agree. Returns are daily fractions; yearly figures assume 252 trading days.

export const TRADING_DAYS = 252;
export const NEED = { "1m": 20, "3m": 63, ytd: 1, "1y": 252, all: 1 };
export const NEED_RATIOS = 63;
export const NEED_ROLLING = 84;
export const NEED_MC = 126;

export const sum = (xs) => xs.reduce((t, x) => t + x, 0);
export const mean = (xs) => (xs.length ? sum(xs) / xs.length : 0);

export function sd(xs) {
  const m = mean(xs);
  return xs.length > 1 ? Math.sqrt(sum(xs.map((x) => (x - m) ** 2)) / (xs.length - 1)) : 0;
}

export function cov(xs, ys) {
  if (xs.length < 2) {
    return 0;
  }
  const mx = mean(xs);
  const my = mean(ys);
  let t = 0;
  for (let i = 0; i < xs.length; i += 1) {
    t += (xs[i] - mx) * (ys[i] - my);
  }
  return t / (xs.length - 1);
}

export const beta = (xs, m) => (sd(m) ? cov(xs, m) / sd(m) ** 2 : 0);
export const correlation = (xs, ys) => (sd(xs) * sd(ys) ? cov(xs, ys) / (sd(xs) * sd(ys)) : 0);
export const compound = (xs) => xs.reduce((v, r) => v * (1 + r), 1) - 1;

export function quantile(sorted, q) {
  if (!sorted.length) {
    return 0;
  }
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

// The days both series have a figure for, e.g. a holding and the portfolio.
export function paired(xs, ys) {
  const a = [];
  const b = [];
  xs.forEach((x, i) => {
    if (x !== null && ys[i] !== null && ys[i] !== undefined) {
      a.push(x);
      b.push(ys[i]);
    }
  });
  return [a, b];
}

export function growth(returns) {
  let v = 100;
  return [100, ...returns.map((r) => (v *= 1 + r))];
}

// The index of the close a period is measured from, for the period ending at `end`.
export function periodStart(dates, period, end) {
  if (period === "1m") return Math.max(0, end - 20);
  if (period === "3m") return Math.max(0, end - 62);
  if (period === "1y") return Math.max(0, end - 252);
  if (period === "ytd") {
    const year = dates[end].slice(0, 4);
    let i = end;
    while (i > 0 && dates[i - 1].slice(0, 4) === year) i -= 1;
    return Math.max(0, i - 1);
  }
  return 0;
}

export function drawdowns(returns) {
  let value = 1;
  let peak = 1;
  let worst = 0;
  let worstAt = 0;
  let peakAt = 0;
  let worstPeakAt = 0;
  const series = [];
  returns.forEach((r, i) => {
    value *= 1 + r;
    if (value > peak) {
      peak = value;
      peakAt = i;
    }
    const fall = value / peak - 1;
    series.push(fall);
    if (fall < worst) {
      worst = fall;
      worstAt = i;
      worstPeakAt = peakAt;
    }
  });
  let recovered = null;
  if (worst < 0) {
    for (let i = worstAt; i < series.length; i += 1) {
      if (series[i] >= 0) {
        recovered = i;
        break;
      }
    }
  }
  return {
    series,
    worst,
    current: series.length ? series[series.length - 1] : 0,
    recoveryDays: recovered === null ? null : recovered - worstPeakAt,
  };
}

export function monthly(dates, returns) {
  const months = [];
  returns.forEach((r, i) => {
    const key = dates[i].slice(0, 7);
    if (!months.length || months[months.length - 1].key !== key) {
      months.push({ key, value: 1 });
    }
    months[months.length - 1].value *= 1 + r;
  });
  return months.map((m) => ({ key: m.key, value: m.value - 1 }));
}

// Everything a factsheet shows, for a window of daily returns, the risk-free rate for each of
// those days, and the benchmark's, if there is one.
export function stats(r, rf, b) {
  const n = r.length;
  const years = n / TRADING_DAYS;
  const total = compound(r);
  const cagr = years >= 1 ? (1 + total) ** (1 / years) - 1 : null;
  const vol = sd(r) * Math.sqrt(TRADING_DAYS);
  const excess = r.map((x, i) => x - rf[i]);
  const sharpe = sd(r) ? (mean(excess) / sd(r)) * Math.sqrt(TRADING_DAYS) : 0;
  const downside = Math.sqrt(mean(excess.map((x) => Math.min(0, x) ** 2)));
  const sortino = downside ? (mean(excess) / downside) * Math.sqrt(TRADING_DAYS) : 0;
  const falls = drawdowns(r);
  const annual = (1 + mean(r)) ** TRADING_DAYS - 1;
  const calmar = falls.worst ? (cagr === null ? annual : cagr) / Math.abs(falls.worst) : 0;
  const sorted = [...r].sort((x, y) => x - y);
  const var95 = -quantile(sorted, 0.05);
  const tail = sorted.filter((x) => x <= -var95);
  const m = mean(r);
  const s = sd(r) || 1;
  const out = {
    days: n,
    total,
    cagr,
    annual,
    vol,
    sharpe,
    sortino,
    calmar,
    maxDD: falls.worst,
    currentDD: falls.current,
    recoveryDays: falls.recoveryDays,
    var95,
    cvar95: -mean(tail),
    best: n ? Math.max(...r) : 0,
    worst: n ? Math.min(...r) : 0,
    hitRate: r.filter((x) => x > 0).length / (n || 1),
    skew: mean(r.map((x) => ((x - m) / s) ** 3)),
    kurt: mean(r.map((x) => ((x - m) / s) ** 4)) - 3,
    benchTotal: null,
    beta: null,
    alpha: null,
    corr: null,
    te: null,
    ir: null,
    upCapture: null,
    downCapture: null,
  };
  if (b) {
    const bb = beta(r, b);
    const rfMean = mean(rf);
    const active = r.map((x, i) => x - b[i]);
    const te = sd(active) * Math.sqrt(TRADING_DAYS);
    const capture = (pick) => {
      const days = r.map((x, i) => [x, b[i]]).filter(([, y]) => pick(y));
      const theirs = mean(days.map(([, y]) => y));
      return theirs ? mean(days.map(([x]) => x)) / theirs : 0;
    };
    Object.assign(out, {
      benchTotal: compound(b),
      beta: bb,
      alpha: (m - rfMean - bb * (mean(b) - rfMean)) * TRADING_DAYS,
      corr: correlation(r, b),
      te,
      ir: te ? (mean(active) * TRADING_DAYS) / te : 0,
      upCapture: capture((y) => y > 0),
      downCapture: capture((y) => y < 0),
    });
  }
  return out;
}

// Each part's points of the return over a window, linked so they add up to the whole.
export function contributions(parts, portfolio) {
  const totals = Object.fromEntries(Object.keys(parts).map((k) => [k, 0]));
  let value = 1;
  let other = 0;
  portfolio.forEach((r, t) => {
    let explained = 0;
    for (const [key, series] of Object.entries(parts)) {
      totals[key] += series[t] * value;
      explained += series[t];
    }
    other += (r - explained) * value;
    value *= 1 + r;
  });
  return { totals, other, total: value - 1 };
}

export const effectiveHoldings = (weights) => {
  const squares = sum(weights.map((w) => w * w));
  return squares ? 1 / squares : 0;
};

// The page's seeded random numbers (mulberry32), so a seed always gives the same futures.
export function seeded(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Futures built from blocks of real days, so the bad weeks come in runs as they really do.
// The 5th, 25th, 50th, 75th and 95th percentiles at each month.
export function monteCarlo(returns, years, seed = 1, paths = 500) {
  const next = seeded(seed);
  const steps = Math.round(years * 12);
  const perStep = 21;
  const block = 10;
  const atStep = Array.from({ length: steps + 1 }, () => []);
  const samples = [];
  for (let p = 0; p < paths; p += 1) {
    let value = 1;
    atStep[0].push(1);
    const track = [1];
    for (let step = 1; step <= steps; step += 1) {
      for (let d = 0; d < perStep; d += block) {
        const start = Math.floor(next() * (returns.length - block));
        for (let k = 0; k < Math.min(block, perStep - d); k += 1) value *= 1 + returns[start + k];
      }
      atStep[step].push(value);
      track.push(value);
    }
    if (p < 3) samples.push(track);
  }
  const bands = atStep.map((values) => {
    values.sort((x, y) => x - y);
    return [0.05, 0.25, 0.5, 0.75, 0.95].map((q) => quantile(values, q));
  });
  const finals = atStep[steps];
  return { bands, samples, loss: finals.filter((v) => v < 1).length / finals.length };
}

// Each holding's beta to the market, then to the part of chips' moves the market doesn't
// explain, so the stress test's two dials don't count the same move twice.
export function sensitivities(returns, market, chips) {
  const chipsBeta = beta(chips, market);
  const chipsOwn = chips.map((c, i) => c - chipsBeta * market[i]);
  const out = {};
  for (const [key, series] of Object.entries(returns)) {
    const days = series.map((x, i) => (x === null ? -1 : i)).filter((i) => i >= 0);
    const mine = days.map((i) => series[i]);
    const m = days.map((i) => market[i]);
    const toMarket = beta(mine, m);
    const leftover = mine.map((x, k) => x - toMarket * m[k]);
    out[key] = { market: toMarket, chips: beta(leftover, days.map((i) => chipsOwn[i])) };
  }
  return out;
}

// Splits the list into two halves of about equal weight, along the longer side, until each
// box holds one thing. Positions are percentages of the whole.
export function treemap(items, x = 0, y = 0, w = 100, h = 100, out = []) {
  if (!items.length) return out;
  if (items.length === 1) {
    out.push({ ...items[0], x, y, w, h });
    return out;
  }
  const total = sum(items.map((i) => i.weight)) || 1;
  let running = 0;
  let split = 1;
  for (let i = 0; i < items.length - 1; i += 1) {
    running += items[i].weight;
    split = i + 1;
    if (running >= total / 2) break;
  }
  const share = sum(items.slice(0, split).map((i) => i.weight)) / total;
  if (w * 1.6 >= h * 1.1) {
    treemap(items.slice(0, split), x, y, w * share, h, out);
    treemap(items.slice(split), x + w * share, y, w * (1 - share), h, out);
  } else {
    treemap(items.slice(0, split), x, y, w, h * share, out);
    treemap(items.slice(split), x, y + h * share, w, h * (1 - share), out);
  }
  return out;
}
