# Deployment

The `Dockerfile` builds a small image that runs as an unprivileged user, with static files already collected. On any platform that runs containers:

1. Set the production environment variables listed in [Configuration](configuration.md).
2. Run `python manage.py migrate` as a release or pre-deploy step rather than on container start, so two instances never migrate at once.
3. Point the platform's health check at `/healthz/`. It answers before host validation and HTTPS redirects, and returns 503 if the database is unreachable.
4. Schedule `python manage.py delete_old_messages` to run daily. It deletes contact messages older than 12 months, as the contact page's privacy note promises. (Old messages are also cleared out whenever a new one arrives, as a fallback.)
5. Schedule `python manage.py update_investments` for each weekday morning (see below).

In production, HTTP redirects to HTTPS, cookies are sent over HTTPS only, and pages carry a strict Content Security Policy.

## The daily investments update

`python manage.py update_investments` downloads the account's Flex report from IBKR and SONIA from the Bank of England, and stores them. Each source is tried on its own, every attempt is logged under Import runs in the admin, and any failure is emailed to `CONTACT_EMAIL` with the command exiting non-zero. It also emails a reminder as the IBKR token's end date nears.

IBKR's report for a day is ready overnight, and the Bank of England publishes SONIA at 10am the next working day, so the update runs mid-morning, Tuesday to Saturday, to pick up Monday to Friday.

On Render, as a cron job:

- **Runtime:** Docker, from the same repository and branch as the web service.
- **Schedule:** `45 10 * * 2-6` (10:45 UTC, so 10:45 in winter and 11:45 in summer, UK time).
- **Command:** `python manage.py update_investments`
- **Environment:** the web service's variables (at least `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `SITE_URL` and the `SMTP_*` ones) plus the three `IBKR_FLEX_*` ones. Environment groups linked to both services keep them in one place.

A day can be fetched by hand from the cron job's page with **Trigger Run**, or anywhere with the same command.

### Prices loaded by hand

Benchmark prices from before a fund was bought (the world shares fund, for instance) come from a CSV of daily closes, as price sites give them:

```
python manage.py import_prices acwi path/to/prices.csv
```

or under Price series in the admin. London prices are usually quoted in pence while IBKR's are in pounds: include a few days that are already kept and the difference is spotted and converted, or pass `--pence`.
