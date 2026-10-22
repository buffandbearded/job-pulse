select
    source || ':' || id as job_key,
    source,
    skill
from {{ source('raw', 'job_skills') }}
