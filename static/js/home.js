// The home page: the console, the globe and code rain, the project screens
// and the intro.

import { initCodeRain } from "./modules/code-rain.js";
import { initConsole } from "./modules/console.js";
import { initGlobe } from "./modules/globe.js";
import { initHeroClock } from "./modules/hero-clock.js";
import { initIntro } from "./modules/intro.js";
import { initProjectScreens } from "./modules/project-screens.js";

initConsole(document.querySelector("[data-console]"));
initHeroClock({
  counter: document.querySelector("[data-hero-counter]"),
  date: document.querySelector("[data-hero-date]"),
});
initGlobe(document.querySelector("[data-globe]"));
initCodeRain(document.querySelector("[data-code-rain]"));
initProjectScreens(document.querySelectorAll("[data-screen]"));
// Last, so everything else is already listening when it starts.
initIntro(document.querySelector("[data-intro-screen]"));
