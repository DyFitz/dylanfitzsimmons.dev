// The contact page and its confirmation: the globe, and the count under the message. The form
// itself needs no script.

import { initMessageCount } from "./modules/message-count.js";
import { initUplinkGlobe } from "./modules/uplink-globe.js";

initUplinkGlobe(document.querySelector("[data-uplink-globe]"));
initMessageCount(
  document.querySelector(".uplink__form textarea"),
  document.querySelector("[data-count]"),
  document.querySelector("[data-packet-state]"),
);
