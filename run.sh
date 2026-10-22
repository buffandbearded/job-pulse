#!/usr/bin/env bash
# One-command pipeline: Postgres -> ingest -> skill extraction -> dbt.
# Usage: ./run.sh   (activate your venv first: source .venv/Scripts/activate)
set -euo pipefail

docker compose up -d
echo "Waiting for Postgres..."
until docker exec job-pulse-db pg_isready -U jobpulse -d jobpulse >/dev/null 2>&1; do sleep 1; done

python src/ingest.py
python src/extract.py
./run_dbt.sh build

echo
echo "Done. Start the services with:"
echo "  uvicorn api.main:app --port 8000     # API docs at http://localhost:8000/docs"
echo "  streamlit run dashboard/app.py       # dashboard at http://localhost:8501"
