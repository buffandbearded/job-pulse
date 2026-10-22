-- Skills that appear together in the same posting.
select
    a.skill as skill_a,
    b.skill as skill_b,
    count(*) as postings_together
from {{ ref('stg_job_skills') }} a
join {{ ref('stg_job_skills') }} b
    on a.job_key = b.job_key and a.skill < b.skill
group by a.skill, b.skill
