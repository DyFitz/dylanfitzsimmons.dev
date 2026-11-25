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
//   data-set-d="{{path}}"       sets the d attribute (any name works), for attributes
//                               such as SVG geometry that a placeholder would make invalid
//   data-hidden="path"          hides the element while the value is truthy
//   <template data-if="path">   present only while the value is truthy
//   <template data-each="path" data-as="name">
//                               once per item; built again if the list's length changes

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

// Inside an <svg>, a <template> isn't a real one and has no content, just children.
function contentOf(template) {
  if (template.content) {
    return template.content;
  }
  const fragment = document.createDocumentFragment();
  fragment.append(...template.childNodes);
  return fragment;
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
      } else if (name.startsWith("data-set-")) {
        element.removeAttribute(name);
        const target = name.slice(9);
        let shown = null;
        updaters.push((values) => {
          const text = fill(value, vars, values);
          if (text !== shown) {
            shown = text;
            element.setAttribute(target, text);
          }
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
            // A field the visitor has changed no longer follows its attribute.
            if (name === "value" && "value" in element) {
              element.value = text;
            }
          }
        });
      }
    }
  };

  const bindEach = (template) => {
    const anchor = document.createComment("");
    const path = template.dataset.each;
    const as = template.dataset.as;
    const content = contentOf(template);
    template.replaceWith(anchor);
    let items = [];
    const make = (length) => {
      items.forEach((item) => item.destroy());
      items = [];
      for (let index = 0; index < length; index += 1) {
        const item = build(content.cloneNode(true), { ...vars, [as]: { list: path, index } }, shared);
        anchor.before(...item.nodes);
        items.push(item);
      }
    };
    make((resolve(path, vars, shared.values) ?? []).length);
    updaters.push((values) => {
      const length = (resolve(path, vars, values) ?? []).length;
      if (length !== items.length) {
        make(length);
      }
      items.forEach((item) => item.update(values));
    });
    cleanups.push(() => items.forEach((item) => item.destroy()));
  };

  const bindIf = (template) => {
    const anchor = document.createComment("");
    const path = template.dataset.if;
    const content = contentOf(template);
    template.replaceWith(anchor);
    let current = null;
    updaters.push((values) => {
      const wanted = Boolean(resolve(path, vars, values));
      if (wanted && !current) {
        current = build(content.cloneNode(true), vars, shared);
        // In place first, so any block inside it that fills itself in lands on the page.
        anchor.before(...current.nodes);
        current.update(values);
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
  container.replaceChildren(...view.nodes);
  view.update(values);
  return (next) => {
    shared.values = next;
    view.update(next);
  };
}
