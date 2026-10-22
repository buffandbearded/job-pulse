import os

import altair as alt
import pandas as pd
import psycopg2
import streamlit as st

DSN = os.getenv(
    "DATABASE_URL",
    "host=localhost port=5433 dbname=jobpulse user=jobpulse password=jobpulse",
)

st.set_page_config(page_title="job-pulse", page_icon="📊", layout="wide")


@st.cache_data(ttl=60)
def load(sql: str, params: tuple = ()) -> pd.DataFrame:
    with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)


st.title("job-pulse")
st.caption("Which skills do remote job postings ask for? Sources: RemoteOK, Arbeitnow, Remotive.")

# --- KPIs -------------------------------------------------------------
kpi = load(
    """
    SELECT (SELECT count(*) FROM analytics_staging.stg_job_postings) AS postings,
           (SELECT count(DISTINCT skill) FROM analytics_staging.stg_job_skills) AS skills,
           (SELECT count(DISTINCT source) FROM analytics_staging.stg_job_postings) AS sources,
           (SELECT max(ingested_at) FROM analytics_staging.stg_job_postings) AS last_ingest
    """
).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Job postings", int(kpi["postings"]))
c2.metric("Distinct skills", int(kpi["skills"]))
c3.metric("Sources", int(kpi["sources"]))
c4.metric("Last ingest (UTC)", f"{kpi['last_ingest']:%Y-%m-%d %H:%M}")

# --- Top skills -------------------------------------------------------
st.subheader("Most demanded skills")
n = st.slider("Number of skills", 5, 40, 15)
top = load(
    "SELECT skill, postings, pct_of_postings::float AS pct_of_postings FROM analytics_marts.mart_skill_demand "
    "ORDER BY postings DESC LIMIT %s",
    (n,),
)
chart = (
    alt.Chart(top)
    .mark_bar()
    .encode(
        x=alt.X("postings:Q", title="Postings mentioning skill"),
        y=alt.Y("skill:N", sort="-x", title=None),
        tooltip=["skill", "postings", "pct_of_postings"],
    )
)
st.altair_chart(chart, width="stretch")

# --- Skill by source --------------------------------------------------
st.subheader("Demand by source")
by_source = load(
    "SELECT source, skill, postings FROM analytics_marts.mart_skill_by_source "
    "WHERE skill IN (SELECT skill FROM analytics_marts.mart_skill_demand "
    "ORDER BY postings DESC LIMIT 10)"
)
chart2 = (
    alt.Chart(by_source)
    .mark_bar()
    .encode(
        x=alt.X("skill:N", title=None),
        y=alt.Y("postings:Q"),
        color="source:N",
        tooltip=["source", "skill", "postings"],
    )
)
st.altair_chart(chart2, width="stretch")

# --- Skill explorer ---------------------------------------------------
st.subheader("Skill explorer")
all_skills = load("SELECT skill FROM analytics_marts.mart_skill_demand ORDER BY postings DESC")["skill"]
skill = st.selectbox("Pick a skill", all_skills, index=0)

left, right = st.columns(2)
with left:
    st.markdown(f"**Skills that appear with `{skill}`**")
    related = load(
        """
        SELECT CASE WHEN skill_a = %(s)s THEN skill_b ELSE skill_a END AS skill,
               postings_together
        FROM analytics_marts.mart_skill_pairs
        WHERE skill_a = %(s)s OR skill_b = %(s)s
        ORDER BY postings_together DESC LIMIT 10
        """.replace("%(s)s", "%s"),
        (skill, skill, skill),
    )
    st.dataframe(related, hide_index=True, width="stretch")
with right:
    st.markdown(f"**Latest postings mentioning `{skill}`**")
    jobs = load(
        """
        SELECT p.title, p.company, p.source, p.url
        FROM analytics_staging.stg_job_postings p
        JOIN analytics_staging.stg_job_skills s USING (job_key)
        WHERE s.skill = %s
        ORDER BY p.published_at DESC NULLS LAST LIMIT 10
        """,
        (skill,),
    )
    st.dataframe(
        jobs,
        hide_index=True,
        width="stretch",
        column_config={"url": st.column_config.LinkColumn("link")},
    )
