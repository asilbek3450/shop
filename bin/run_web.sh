#!/usr/bin/env bash
set -e

if [ "${RESET_DB}" = "1" ]; then
  echo "⚠️  RESET_DB=1 — wiping public schema before migration"
  python manage.py wipe_db --i-mean-it
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 120 --log-file -
