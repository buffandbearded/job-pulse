import sys
from pathlib import Path

import psycopg2
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import DSN, app  # noqa: E402

try:
    psycopg2.connect(DSN).close()
    DB_UP = True
except psycopg2.OperationalError:
    DB_UP = False

pytestmark = pytest.mark.skipif(not DB_UP, reason="Postgres not running")
client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_top_skills_sorted():
    rows = client.get("/skills/top?limit=5").json()
    assert len(rows) == 5
    counts = [r["postings"] for r in rows]
    assert counts == sorted(counts, reverse=True)


def test_unknown_skill_404():
    assert client.get("/skills/definitely-not-a-skill").status_code == 404
