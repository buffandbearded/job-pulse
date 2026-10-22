select
    source,
    skill,
    count(distinct job_key) as postings
from {{ ref('stg_job_skills') }}
group by source, skill
