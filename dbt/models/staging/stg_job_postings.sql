-- One row per job posting, with the three sources mapped onto common columns.
select
    source,
    id,
    source || ':' || id as job_key,
    case source
        when 'remoteok' then payload ->> 'position'
        else payload ->> 'title'
    end as title,
    case source
        when 'remoteok' then payload ->> 'company'
        else payload ->> 'company_name'
    end as company,
    case source
        when 'remotive' then payload ->> 'candidate_required_location'
        else payload ->> 'location'
    end as location,
    payload ->> 'url' as url,
    case source
        when 'arbeitnow' then to_timestamp((payload ->> 'created_at')::bigint)
        when 'remotive' then (payload ->> 'publication_date')::timestamptz
        else (payload ->> 'date')::timestamptz
    end as published_at,
    ingested_at
from {{ source('raw', 'job_postings') }}
