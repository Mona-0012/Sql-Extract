SET search_path to {schema};

CREATE TABLE IF NOT EXISTS rule_detect_external_table_inside_joins (
rule_id BIGINT,
org_id TEXT,
version_id BIGINT,
project_name TEXT,
log_id TEXT,
user_name TEXT,
query TEXT,
schema_name TEXT,
table_name TEXT,
entity_type TEXT
);

WITH filtered_base_query_info AS (
    SELECT *
    FROM base_query_info b
    WHERE b.relationship_type = 'JOINS' AND b.version_id=:version_id
)
SELECT DISTINCT
    14 AS rule_id,
    'hsbc' AS org_id,
    b.version_id,
    b.log_id,
    b.user_name,
    b.query,
    v.database_name AS project_name,
    v.schema_name,
    v.table_name,
    v.entity_type
FROM filtered_base_query_info b
CROSS JOIN LATERAL (
    SELECT b.source_database     AS database_name,
           b.source_schema       AS schema_name,
           b.source_entity_name  AS table_name,
           b.source_entity_type  AS entity_type
    WHERE b.source_entity_type = 'EXTERNAL_TABLE'
    
    UNION ALL

    SELECT b.target_database     AS database_name,
           b.target_schema       AS schema_name,
           b.target_entity_name  AS table_name,
           b.target_entity_type  AS entity_type
    WHERE b.target_entity_type = 'EXTERNAL_TABLE'
) v;
