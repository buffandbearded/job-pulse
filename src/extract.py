import html
import re

import psycopg2

from skills import SKILLS

DSN = "host=localhost port=5433 dbname=jobpulse user=jobpulse password=jobpulse"

DDL = """
CREATE TABLE IF NOT EXISTS raw.job_skills (
    source TEXT NOT NULL,
    id TEXT NOT NULL,
    skill TEXT NOT NULL,
    PRIMARY KEY (source, id, skill)
);
"""

COMPILED = {
    skill: [re.compile(p, re.IGNORECASE) for p in patterns]
    for skill, patterns in SKILLS.items()
}

TAG_RE = re.compile(r"<[^>]+>")


def clean_text(payload: dict) -> str:
    parts = [
        payload.get("title") or payload.get("position") or "",
        payload.get("description") or "",
        " ".join(payload.get("tags") or []),
    ]
    text = html.unescape(TAG_RE.sub(" ", " ".join(parts)))
    return text.lower()


def extract_skills(text: str) -> set:
    return {
        skill
        for skill, patterns in COMPILED.items()
        if any(p.search(text) for p in patterns)
    }


def run():
    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        cur.execute("TRUNCATE raw.job_skills")
        cur.execute("SELECT source, id, payload FROM raw.job_postings")
        rows = cur.fetchall()
        total = 0
        for source, job_id, payload in rows:
            for skill in extract_skills(clean_text(payload)):
                cur.execute(
                    "INSERT INTO raw.job_skills (source, id, skill) VALUES (%s, %s, %s)",
                    (source, job_id, skill),
                )
                total += 1
    print(f"Processed {len(rows)} postings, wrote {total} skill rows")


if __name__ == "__main__":
    run()
