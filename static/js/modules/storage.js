// Remembers settings in localStorage, or sessionStorage for the current visit.
// Storage can throw, e.g. with cookies blocked, and then nothing is
// remembered, which is fine. head.js reads the same keys before first paint.

const area = (session) => (session ? window.sessionStorage : window.localStorage);

export function recall(key, { session = false } = {}) {
  try {
    return area(session).getItem(key);
  } catch {
    return null;
  }
}

export function remember(key, value, { session = false } = {}) {
  try {
    area(session).setItem(key, value);
  } catch {
    // Not fatal; the setting just won't last beyond this page.
  }
}
