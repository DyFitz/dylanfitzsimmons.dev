// Keeps the count under the contact form's message up to date as it's typed. Without it, the
// count shows what was there when the page loaded.

export function initMessageCount(textarea, count, state) {
  if (!textarea || !count) {
    return;
  }
  const update = () => {
    count.textContent = String(textarea.value.length);
    if (state) {
      state.textContent = textarea.value.trim() ? " · packet ready" : " · packet empty";
    }
  };
  textarea.addEventListener("input", update);
  update();
}
