#!/bin/sh
# Entry point of the production image (Dockerfile at the repository root).
set -eu

if [ "${DJANGO_MIGRATE_ON_START:-True}" = "True" ]; then
    python manage.py migrate --noinput
fi

# Idempotent: loads the fictional demo data only where it is missing.
if [ "${DEMO_SEED_ON_START:-False}" = "True" ]; then
    python manage.py demo_seed
fi

exec "$@"
