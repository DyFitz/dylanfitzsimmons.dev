// Every page: the theme and motion buttons and the readout in the header.

import { initBrand } from "./modules/brand.js";
import { followSystemSetting, initMotionToggle } from "./modules/motion.js";
import { initThemeToggle } from "./modules/theme.js";

initThemeToggle(document.querySelector("[data-theme-toggle]"));
initMotionToggle(document.querySelector("[data-motion-toggle]"));
followSystemSetting();
initBrand(document.querySelector("[data-brand]"));
