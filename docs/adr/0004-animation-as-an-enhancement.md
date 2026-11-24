# 4. Animation as an enhancement, with a still version of every page

- Status: accepted
- Date: 2026-11-14

## Context

The home page is built around animation: a boot-up intro, a console typing commands, a turning globe, code rain and animated project screens. Not every visitor can or should see it. Some ask their system for reduced motion, some browse with data saver on, some devices are too slow to keep it smooth, and some browsers run no JavaScript at all. The site has to look deliberate for all of them, not broken.

## Decision

The server always sends the still version of a page. Every animation has a still counterpart in the HTML: an image for the globe and code rain, an SVG for each project screen, and the first console script already finished.

A small script in `<head>` decides before first paint whether anything moves, and records it as `data-motion` on `<html>`. Motion is on unless the visitor has turned it off with the motion button, their system asks for reduced motion, data saver is on, the browser is older than 2022, or the device has already proved too slow on this visit. CSS animations and canvases only run under `data-motion="on"`. A choice made with the motion button always wins.

The animations are plain JavaScript modules, with no build step (see ADR 1). One `requestAnimationFrame` loop drives them all, and each runs only while it's on screen and the tab is visible. The loop watches the frame rate: below 20 frames a second for two samples in a row, the page switches to its still version for the rest of the visit.

Static files are served with hashed names, and the storage backend rewrites the paths in `import` statements to match, so browsers never mix modules from different deploys.

## Consequences

- Every page works without JavaScript or motion, and low-powered devices aren't asked to do more than they can.
- Each animation has two versions to keep in step: its drawing code and its still image. Changing a colour in `main.css` changes both, but changing a shape means editing both.
- Rewriting module imports is a newer Django feature, so a test runs `collectstatic` over the real files. A problem fails the tests rather than the Docker build.
