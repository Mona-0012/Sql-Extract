SET search_path to {schema};


CREATE TABLE IF NOT EXISTS rule_detect_suboptimal_join_order (
    rule_id BIGINT,
    org_id TEXT,
    version_id BIGINT,
    project_name TEXT,
    log_id TEXT,
    user_name TEXT,
    query TEXT,
    left_table_database TEXT,
    left_table_schema TEXT,
    left_table_name TEXT,
    left_table_size_mb NUMERIC(38,2),
    right_table_database TEXT,
    right_table_schema TEXT,
    right_table_name TEXT,
    right_table_size_mb NUMERIC(38,2)
    
);


WITH filtered_base_query_info AS (
    SELECT *
    FROM base_query_info b
    WHERE b.relationship_type = 'JOINS' AND b.version_id={version}
)

INSERT INTO rule_detect_suboptimal_join_order
SELECT DISTINCT
    15 AS rule_id,
    'hsbc' AS org_id,
    b.version_id,
    b.target_database AS project_name,   
    b.log_id,
    b.user_name,
    b.query,
    b.source_database AS left_table_database,
    b.source_schema AS left_table_schema,                      
    b.source_entity_name AS left_table_name,  
    tm.size_mb AS left_table_size_mb,
    b.target_database AS right_table_database,
    b.target_schema AS right_table_schema,                       
    b.target_entity_name AS right_table_name,  
    b.table_size AS right_table_size_mb
    
FROM filtered_base_query_info b
INNER JOIN table_metadata tm
    ON tm.database = b.source_database
   AND tm.schema = b.source_schema
   AND tm.table_name = b.source_entity_name
   AND tm.size_mb > b.table_size;
