SELECT * FROM AMH_FZ_FDR_DEV_SIT.TABLES__ t1 JOIN AMH_FZ_FDR_DEV_SIT.event_store t2 ON t1.type=(cast(t2.auth_cam_level AS INT64) limit 50;




SELECT * FROM AMH_FZ_FDR_DEV_SIT.TABLES__ t1 JOIN AMH_FZ_FDR_DEV_SIT.TABLES t2 ON t1.table_id=t2.table_name limit 10;



SELECT t1.table_id AS left_table, ROUND(t1.size_bytes/(1024*1024),2) AS left_size_mb,
t2.table_id AS right_table, ROUND(t2.size_bytes/(1024*1024),2) AS right_size_mb FROM AMH_FZ_FDR_DEV_SIT.TABLES__ t1 JOIN AMH_FZ_FDR_DEV_SIT.TABLES__ t2 ON t1.table_id!=t2.table_id WHERE t1.size_bytes>t2.size_bytes ORDER BY left_size_mb DESC limit 10;
