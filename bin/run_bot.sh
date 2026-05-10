#!/usr/bin/env bash
set -e

if [ "${RESET_DB}" = "1" ]; then
  echo "⚠️  RESET_DB=1 — wiping public schema before migration"
  python manage.py wipe_db --i-mean-it
fi

python manage.py migrate --noinput
python manage.py seed_catalog
exec python manage.py runbot
