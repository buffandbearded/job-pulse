-- How many postings mention each skill, overall and as a share of all postings.
with totals as (
    select count(*) as total_postings from {{ ref('stg_job_postings') }}
)

select
    s.skill,
    count(distinct s.job_key) as postings,
    round(100.0 * count(distinct s.job_key) / t.total_postings, 1) as pct_of_postings
from {{ ref('stg_job_skills') }} s
cross join totals t
group by s.skill, t.total_postings
order by postings desc
