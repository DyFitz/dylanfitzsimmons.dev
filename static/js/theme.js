// Applies the saved theme before first paint, then sets up the toggle. Without
// JavaScript the site just follows the OS theme.
(() => {
  "use strict";

  const STORAGE_KEY = "theme";
  const root = document.documentElement;
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

  const readSavedTheme = () => {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return value === "light" || value === "dark" ? value : null;
    } catch {
      return null; // localStorage can throw, e.g. in some private windows.
    }
  };

  const saveTheme = (theme) => {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Not fatal; the choice just won't be remembered.
    }
  };

  const activeTheme = () => root.dataset.theme ?? (prefersDark.matches ? "dark" : "light");
  const oppositeTheme = () => (activeTheme() === "dark" ? "light" : "dark");

  const savedTheme = readSavedTheme();
  if (savedTheme) {
    root.dataset.theme = savedTheme;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector("[data-theme-toggle]");
    if (!toggle) {
      return;
    }

    const updateLabel = () => {
      toggle.textContent = `Switch to ${oppositeTheme()} theme`;
    };

    toggle.addEventListener("click", () => {
      const theme = oppositeTheme();
      root.dataset.theme = theme;
      saveTheme(theme);
      updateLabel();
    });

    // Keeps the label right if the OS theme changes while nothing is saved.
    prefersDark.addEventListener("change", updateLabel);

    updateLabel();
    toggle.hidden = false;
  });
})();
