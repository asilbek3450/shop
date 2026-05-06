# Railway Deployment

This repository is prepared for two Railway services from the same codebase:

1. `web`
   Start command:
   `./bin/run_web.sh`

2. `bot`
   Start command:
   `./bin/run_bot.sh`

Recommended shared variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=.up.railway.app,.railway.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://*.up.railway.app,https://*.railway.app`
- `DATABASE_URL`
- `SITE_URL`
- `TELEGRAM_BOT_TOKEN`

Seed local data:

`python manage.py seed_catalog`

Run locally:

- Web: `python manage.py runserver`
- Bot: `python manage.py runbot`
