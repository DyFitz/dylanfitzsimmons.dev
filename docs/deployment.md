# Deployment

The `Dockerfile` builds a small image that runs as an unprivileged user, with static files already collected. On any platform that runs containers:

1. Set the production environment variables listed in [Configuration](configuration.md).
2. Run `python manage.py migrate` as a release or pre-deploy step rather than on container start, so two instances never migrate at once.
3. Point the platform's health check at `/healthz/`. It answers before host validation and HTTPS redirects, and returns 503 if the database is unreachable.
4. Schedule `python manage.py delete_old_messages` to run daily. It deletes contact messages older than 12 months, as the contact page's privacy note promises. (Old messages are also cleared out whenever a new one arrives, as a fallback.)

In production, HTTP redirects to HTTPS, cookies are sent over HTTPS only, and pages carry a strict Content Security Policy.
