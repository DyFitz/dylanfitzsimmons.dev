// The projects page. Where head.js has decided the monitor will be shown (a wide enough
// screen, and a browser that can run it), the plain list of projects is swapped for a
// monitor in a room; on a phone, for the '95 desktop filling the screen. Anywhere else the
// list stays as it is. A visitor who has chosen the list keeps it, with a button to go back.

import { Desk } from "./modules/desk.js";
import { offerDesk } from "./modules/list-choice.js";
import { startPhoneDesk } from "./modules/phone-desk.js";

const { desk: mode, deskOff } = document.documentElement.dataset;
const data = document.getElementById("projects-data");
const picker = document.querySelector("[data-desk-picker]");
const room = document.querySelector("[data-desk-room]");

if (mode === "phone") {
  startPhoneDesk(document.getElementById("desk-phone-template"));
} else if (data && picker && room && mode) {
  const { projects, urls, images, cv } = JSON.parse(data.textContent);
  new Desk({
    projects,
    urls,
    images,
    cv,
    picker,
    room,
    pickerTemplate: document.getElementById("desk-picker-template"),
    roomTemplate: document.getElementById("desk-room-template"),
  }).start();
} else if (deskOff) {
  offerDesk(deskOff);
}
