import os

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query

DSN = os.getenv(
    "DATABASE_URL",
    "host=localhost port=5433 dbname=jobpulse user=jobpulse password=jobpulse",
)

app = FastAPI(
    title="job-pulse API",
    description="Skill demand in remote job postings (RemoteOK, Arbeitnow, Remotive).",
    version="1.0.0",
)


def query(sql: str, params: tuple = ()) -> list:
    with psycopg2.connect(DSN) as conn, conn.cursor(
        cursor_factory=psycopg2.extras.RealDictCursor
    ) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


@app.get("/health")
def health():
    query("SELECT 1")
    return {"status": "ok"}


@app.get("/skills/top")
def top_skills(limit: int = Query(20, ge=1, le=100)):
    """Most demanded skills across all postings."""
    return query(
        "SELECT skill, postings, pct_of_postings "
        "FROM analytics_marts.mart_skill_demand ORDER BY postings DESC LIMIT %s",
        (limit,),
    )


@app.get("/skills/{skill}")
def skill_detail(skill: str):
    """Demand for one skill, overall and per source."""
    overall = query(
        "SELECT skill, postings, pct_of_postings "
        "FROM analytics_marts.mart_skill_demand WHERE skill = %s",
        (skill.lower(),),
    )
    if not overall:
        raise HTTPException(status_code=404, detail=f"Unknown skill: {skill}")
    by_source = query(
        "SELECT source, postings FROM analytics_marts.mart_skill_by_source "
        "WHERE skill = %s ORDER BY postings DESC",
        (skill.lower(),),
    )
    return {**overall[0], "by_source": by_source}


@app.get("/skills/{skill}/related")
def related_skills(skill: str, limit: int = Query(10, ge=1, le=50)):
    """Skills that most often appear in the same posting as this one."""
    rows = query(
        """
        SELECT CASE WHEN skill_a = %(s)s THEN skill_b ELSE skill_a END AS skill,
               postings_together
        FROM analytics_marts.mart_skill_pairs
        WHERE skill_a = %(s)s OR skill_b = %(s)s
        ORDER BY postings_together DESC
        LIMIT %(n)s
        """,
        {"s": skill.lower(), "n": limit},
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for skill: {skill}")
    return rows


@app.get("/jobs")
def jobs(skill: str, limit: int = Query(20, ge=1, le=100)):
    """Job postings that mention a skill, newest first."""
    return query(
        """
        SELECT p.title, p.company, p.location, p.url, p.published_at, p.source
        FROM analytics_staging.stg_job_postings p
        JOIN analytics_staging.stg_job_skills s USING (job_key)
        WHERE s.skill = %s
        ORDER BY p.published_at DESC NULLS LAST
        LIMIT %s
        """,
        (skill.lower(), limit),
    )
