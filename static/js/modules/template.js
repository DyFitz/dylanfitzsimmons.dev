// Fills an HTML <template> from a plain object of values and keeps it in step as
// the values change. Written for the projects page, whose markup has too many
// moving parts to update by hand. In the markup:
//
//   {{path}}                    in text or an attribute: the value at that path
//   data-on-click="path"        calls the function at that path (any event name)
//   data-ref="path"             hands the element to the function at that path
//   data-style="left: {{x}}%"   sets styles through the CSSOM, which the site's
//                               Content Security Policy allows where a style
//                               attribute would be blocked
//   data-hidden="path"          hides the element while the value is truthy
//   <template data-if="path">   present only while the value is truthy
//   <template data-each="path" data-as="name">
//                               once per item; the list's length is read once

const HOLE = /\{\{\s*([\w.]+)\s*\}\}/g;

// A path is looked up in the loop variables first, then in the values.
function resolve(path, vars, values) {
  const [first, ...rest] = path.split(".");
  let value;
  if (first in vars) {
    const { list, index } = vars[first];
    value = resolve(list, vars, values)?.[index];
  } else {
    value = values[first];
  }
  for (const key of rest) {
    value = value?.[key];
  }
  return value;
}

const fill = (text, vars, values) =>
  text.replace(HOLE, (_, path) => resolve(path, vars, values) ?? "");

function applyStyle(element, text, previous) {
  const next = new Map();
  for (const declaration of text.split(";")) {
    const colon = declaration.indexOf(":");
    if (colon > 0) {
      next.set(declaration.slice(0, colon).trim(), declaration.slice(colon + 1).trim());
    }
  }
  for (const name of previous.keys()) {
    if (!next.has(name)) {
      element.style.removeProperty(name);
    }
  }
  for (const [name, value] of next) {
    if (previous.get(name) !== value) {
      element.style.setProperty(name, value);
    }
  }
  return next;
}

// Builds the live nodes for one copy of a template's content. `shared.values`
// always holds the latest values, for event handlers to read when they fire.
function build(fragment, vars, shared) {
  const updaters = [];
  const cleanups = [];

  const bindElement = (element) => {
    for (const { name, value } of [...element.attributes]) {
      if (name.startsWith("data-on-")) {
        element.removeAttribute(name);
        element.addEventListener(name.slice(8), (event) => {
          const handler = resolve(value, vars, shared.values);
          if (typeof handler === "function") {
            handler(event);
          }
        });
      } else if (name === "data-ref") {
        element.removeAttribute(name);
        resolve(value, vars, shared.values)?.(element);
        cleanups.push(() => resolve(value, vars, shared.values)?.(null, element));
      } else if (name === "data-style") {
        element.removeAttribute(name);
        let applied = new Map();
        updaters.push((values) => {
          applied = applyStyle(element, fill(value, vars, values), applied);
        });
      } else if (name === "data-hidden") {
        element.removeAttribute(name);
        updaters.push((values) => {
          element.hidden = Boolean(resolve(value, vars, values));
        });
      } else if (value.includes("{{")) {
        let shown = null;
        updaters.push((values) => {
          const text = fill(value, vars, values);
          if (text !== shown) {
            shown = text;
            element.setAttribute(name, text);
          }
        });
      }
    }
  };

  const bindEach = (template) => {
    const list = resolve(template.dataset.each, vars, shared.values) ?? [];
    for (let index = 0; index < list.length; index += 1) {
      const item = build(
        template.content.cloneNode(true),
        { ...vars, [template.dataset.as]: { list: template.dataset.each, index } },
        shared,
      );
      template.before(...item.nodes);
      updaters.push(item.update);
      cleanups.push(item.destroy);
    }
    template.remove();
  };

  const bindIf = (template) => {
    const anchor = document.createComment("");
    const path = template.dataset.if;
    const content = template.content;
    template.replaceWith(anchor);
    let current = null;
    updaters.push((values) => {
      const wanted = Boolean(resolve(path, vars, values));
      if (wanted && !current) {
        current = build(content.cloneNode(true), vars, shared);
        current.update(values);
        anchor.before(...current.nodes);
      } else if (!wanted && current) {
        current.destroy();
        current = null;
      } else if (current) {
        current.update(values);
      }
    });
    cleanups.push(() => current?.destroy());
  };

  const walk = (parent) => {
    for (const node of [...parent.childNodes]) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.nodeValue;
        if (!text.trim() && !text.includes(" ")) {
          // Line breaks between tags in the source aren't meant to be seen.
          node.remove();
        } else if (text.includes("{{")) {
          let shown = null;
          updaters.push((values) => {
            const next = fill(text, vars, values);
            if (next !== shown) {
              shown = next;
              node.nodeValue = next;
            }
          });
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.localName === "template" && node.dataset.each) {
          bindEach(node);
        } else if (node.localName === "template" && node.dataset.if) {
          bindIf(node);
        } else {
          bindElement(node);
          walk(node);
        }
      }
    }
  };

  walk(fragment);
  const nodes = [...fragment.childNodes];
  return {
    nodes,
    update: (values) => updaters.forEach((update) => update(values)),
    destroy: () => {
      cleanups.forEach((cleanup) => cleanup());
      nodes.forEach((node) => node.remove());
    },
  };
}

// Puts a filled copy of the template into the container, in place of whatever
// was there, and returns a function to call with new values.
export function mount(template, container, values) {
  const shared = { values };
  const view = build(template.content.cloneNode(true), {}, shared);
  view.update(values);
  container.replaceChildren(...view.nodes);
  return (next) => {
    shared.values = next;
    view.update(next);
  };
}
