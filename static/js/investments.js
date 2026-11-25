// The investments page. The page the server sends is complete on its own; this swaps it for
// the interactive board, with the switch to the terminal, wherever scripts run.

import { Board } from "./modules/invest-board.js";

const data = document.getElementById("iv-data");
const boardSlot = document.querySelector("[data-iv-board]");
const switchSlot = document.querySelector("[data-iv-switch]");
const boardTemplate = document.getElementById("iv-board-template");
const switchTemplate = document.getElementById("iv-switch-template");

if (data && boardSlot && switchSlot && boardTemplate && switchTemplate) {
  const thinking = document.querySelector("[data-iv-thinking]")?.cloneNode(true);
  new Board({
    data: JSON.parse(data.textContent),
    switchTemplate,
    switchSlot,
    boardTemplate,
    boardSlot,
    thinking,
  }).start();
  document.documentElement.dataset.ivLive = "on";
}
