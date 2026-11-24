// A project's write-up. The preview in the window at the top is drawn the same way as the
// project cards on the home page, and so are the two at the foot of the page.

import { initProjectScreens } from "./modules/project-screens.js";

initProjectScreens(document.querySelectorAll("[data-screen]"));
