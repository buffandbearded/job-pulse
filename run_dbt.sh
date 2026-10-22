#!/usr/bin/env bash
# Runs dbt inside Docker on the job-pulse network. Usage: ./run_dbt.sh build
export MSYS_NO_PATHCONV=1
docker run --rm --network job-pulse_default \
  -v "$(pwd -W 2>/dev/null || pwd)/dbt:/usr/app" -w /usr/app \
  ghcr.io/dbt-labs/dbt-postgres:1.9.latest "${@:-build}" --profiles-dir .
