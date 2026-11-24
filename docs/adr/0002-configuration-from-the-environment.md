# 2. Configuration from the environment

- Status: accepted
- Date: 2026-11-08

## Context

The site runs in three places: a laptop, CI and production. Each needs a different database, different host names and different secrets, and secrets must never be committed to the repository.

## Decision

- Read secrets and anything environment-specific from environment variables, using django-environ.
- Split the settings into `base`, which describes how the site works, and `development`, `test` and `production` modules that override only what differs.
- In production, required values have no defaults. The site refuses to start if one is missing, and the tests prove it.
- Allow a `.env` file for local convenience only. Real environment variables always take precedence over it, and the container image ignores it entirely.

## Consequences

- The same image runs anywhere; only its environment changes.
- Misconfiguration fails loudly at start-up instead of running with an unsafe default.
- Each new setting needs a decision: does it belong in `base`, or does it vary by environment?
