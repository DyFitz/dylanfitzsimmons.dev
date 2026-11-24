// Lets the header readout and the console wait for the intro, without loading
// the intro itself on pages that don't have one. intro.js sends the events.

const root = document.documentElement;

// The console has finished opening this long after the scan line starts.
const ENTRANCE_MS = 1150;

export const introShowing = () => ["pending", "playing"].includes(root.dataset.intro);

export const announceIntro = (stage) => document.dispatchEvent(new Event(`intro${stage}`));

/**
 * onStart runs when the intro starts. onEnd runs once the page has come in
 * after it, unless the intro starts again first.
 */
export function followIntro({ onStart, onEnd }) {
  let timer = 0;
  document.addEventListener("introstart", () => {
    clearTimeout(timer);
    onStart();
  });
  document.addEventListener("introreveal", () => {
    clearTimeout(timer);
    timer = setTimeout(onEnd, ENTRANCE_MS);
  });
}
