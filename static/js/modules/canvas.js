// Sizes the canvases for sharp lines on any screen.

const sizes = new WeakMap();

// Watching sizes saves reading clientWidth every frame, which can force a layout.
const resizeObserver = new ResizeObserver((entries) => {
  for (const { target, contentRect } of entries) {
    sizes.set(target, { width: contentRect.width, height: contentRect.height });
  }
});

/**
 * Matches a canvas's pixels to its size on screen, at up to maxScale pixels
 * per CSS pixel, and clears it unless told not to. Returns null while the
 * canvas isn't displayed.
 */
export function prepare(canvas, { maxScale = 2, clear = true } = {}) {
  if (!sizes.has(canvas)) {
    sizes.set(canvas, { width: 0, height: 0 });
    resizeObserver.observe(canvas);
  }
  const { width, height } = sizes.get(canvas);
  if (!width || !height) {
    return null;
  }
  const scale = Math.min(window.devicePixelRatio || 1, maxScale);
  const pixelWidth = Math.round(width * scale);
  const pixelHeight = Math.round(height * scale);
  const resized = canvas.width !== pixelWidth || canvas.height !== pixelHeight;
  if (resized) {
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;
  }
  const context = canvas.getContext("2d");
  context.setTransform(scale, 0, 0, scale, 0, 0);
  if (clear) {
    context.clearRect(0, 0, width, height);
  }
  return { context, width, height, scale, resized };
}
