// Reads colours and fonts from main.css, so they're only defined there.

export function cssValue(name, element = document.documentElement) {
  return getComputedStyle(element).getPropertyValue(name).trim();
}

/**
 * A colour kept as channels in main.css, e.g. --accent-rgb, as a function
 * that gives it at any opacity: accent(0.5) is "rgba(141, 242, 189, 0.5)".
 */
export function cssColour(name) {
  const channels = cssValue(name).split(/\s+/).join(", ");
  return (alpha = 1) => `rgba(${channels}, ${alpha})`;
}
