// The CV page: lights the section being read in the index and the jump strip, and slides the
// strip along to keep it in view. The links work without it.

const links = [...document.querySelectorAll("[data-section-link]")];
const sections = [...new Set(links.map((link) => link.hash.slice(1)))]
  .map((id) => document.getElementById(id))
  .filter(Boolean);
const strip = document.querySelector(".jump__list");

function light(id) {
  for (const link of links) {
    if (link.hash === `#${id}`) {
      link.setAttribute("aria-current", "true");
    } else {
      link.removeAttribute("aria-current");
    }
  }
  const current = strip?.querySelector(`[href="#${id}"]`);
  if (strip && current && strip.offsetParent) {
    strip.scrollTo({ left: current.offsetLeft - (strip.clientWidth - current.offsetWidth) / 2 });
  }
}

if (sections.length) {
  // The current section is the last one whose heading has passed the top fifth of the screen.
  let lit = "";
  const update = () => {
    const line = window.innerHeight / 5;
    let current = sections[0].id;
    for (const section of sections) {
      if (section.getBoundingClientRect().top < line) {
        current = section.id;
      }
    }
    if (current !== lit) {
      lit = current;
      light(current);
    }
  };
  let queued = false;
  window.addEventListener(
    "scroll",
    () => {
      if (!queued) {
        queued = true;
        requestAnimationFrame(() => {
          queued = false;
          update();
        });
      }
    },
    { passive: true },
  );
  update();
}
