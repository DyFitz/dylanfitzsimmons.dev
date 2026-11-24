// The camcorder readouts in the hero: a running SP counter, which only counts
// while motion is on, and the date and time.

import { isMotionOn } from "./motion.js";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const pad = (n) => String(n).padStart(2, "0");

// The same format as the page is served with; the CSS puts it in capitals.
const stamp = (date) =>
  `${pad(date.getDate())} ${MONTHS[date.getMonth()]} ${date.getFullYear()} ` +
  `${pad(date.getHours())}:${pad(date.getMinutes())}`;

export function initHeroClock({ counter, date }) {
  let seconds = 0;

  const showDate = () => {
    const text = stamp(new Date());
    if (date && date.textContent !== text) {
      date.textContent = text;
    }
  };

  setInterval(() => {
    if (counter && isMotionOn() && !document.hidden) {
      seconds += 1;
      counter.textContent =
        `${Math.floor(seconds / 3600)}:${pad(Math.floor(seconds / 60) % 60)}:${pad(seconds % 60)}`;
    }
    showDate();
  }, 1000);

  // The server's clock is UK time, so this switches it to the visitor's.
  showDate();
}
