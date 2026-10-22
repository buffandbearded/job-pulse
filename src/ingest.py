import json
import requests
import psycopg2

DSN = "host=localhost port=5433 dbname=jobpulse user=jobpulse password=jobpulse"
HEADERS = {"User-Agent": "job-pulse portfolio project (github.com/buffandbearded/job-pulse)"}

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.job_postings (
    source TEXT NOT NULL,
    id TEXT NOT NULL,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, id)
);
"""


def get_json(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_remotive():
    jobs = get_json("https://remotive.com/api/remote-jobs")["jobs"]
    return [(str(j["id"]), j) for j in jobs]


def fetch_remoteok():
    data = get_json("https://remoteok.com/api")
    # first element is a legal notice, not a job
    return [(str(j["id"]), j) for j in data if isinstance(j, dict) and j.get("id")]


def fetch_arbeitnow(pages=5):
    out = []
    for page in range(1, pages + 1):
        data = get_json(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        jobs = data.get("data", [])
        if not jobs:
            break
        out += [(j["slug"], j) for j in jobs if j.get("remote")]
    return out


SOURCES = {
    "remotive": fetch_remotive,
    "remoteok": fetch_remoteok,
    "arbeitnow": fetch_arbeitnow,
}


def load(source, rows):
    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        for job_id, job in rows:
            cur.execute(
                """
                INSERT INTO raw.job_postings (source, id, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (source, id) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (source, job_id, json.dumps(job)),
            )
    return len(rows)


if __name__ == "__main__":
    for name, fetch in SOURCES.items():
        try:
            n = load(name, fetch())
            print(f"{name}: loaded {n} postings")
        except Exception as exc:
            print(f"{name}: FAILED - {exc}")
