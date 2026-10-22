import json
import requests
import psycopg2

URL = "https://remotive.com/api/remote-jobs"
DSN = "host=localhost port=5433 dbname=jobpulse user=jobpulse password=jobpulse"

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.job_postings (
    id BIGINT PRIMARY KEY,
    payload JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def fetch_jobs():
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    return resp.json()["jobs"]


def load(jobs):
    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        for job in jobs:
            cur.execute(
                """
                INSERT INTO raw.job_postings (id, payload)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload
                """,
                (job["id"], json.dumps(job)),
            )
    return len(jobs)


if __name__ == "__main__":
    n = load(fetch_jobs())
    print(f"Loaded {n} job postings")
