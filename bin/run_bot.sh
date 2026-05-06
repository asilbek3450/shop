#!/usr/bin/env bash
set -e
python manage.py migrate --noinput
python manage.py seed_catalog
exec python manage.py runbot
