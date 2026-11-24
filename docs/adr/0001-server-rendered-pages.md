# 1. Server-rendered pages, not a single-page app

- Status: accepted
- Date: 2026-11-08

## Context

The site is mostly content: projects, a CV and a portfolio summary, plus one form. It needs to load quickly, be found by search engines, work well with screen readers, and be easy to change. The interactive parts are small: filtering projects, submitting the contact form and drawing a few charts.

A single-page app (React or similar, talking to a Django REST API) would mean two codebases, a JavaScript build pipeline, client-side routing and validation written twice, for little benefit to a site like this.

## Decision

Render every page on the server with Django templates. Add behaviour with small amounts of JavaScript as progressive enhancement: every page works without it, and scripts make it smoother.

Where a page needs partial updates, such as the contact form or project filters, use htmx with Django's template partials rather than a client-side framework. Draw charts with a small charting library.

Keep all JavaScript and CSS compatible with a strict Content Security Policy: no inline scripts or styles.

## Consequences

- One codebase and one deployment, with no JavaScript build step.
- Pages are fast and accessible by default, and search engines can read them without extra work.
- Highly interactive features are harder to build this way. If the portfolio ever needs one, it can be an isolated component on that page rather than a reason to rewrite the site.
