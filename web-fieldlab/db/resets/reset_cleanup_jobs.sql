USE sql_training;
DELETE FROM cleanup_jobs;
INSERT INTO cleanup_jobs (target_table, expire_token, operator, note) VALUES
('audit_logs',    'TOKEN-EXPIRED-001', 'system',  '默认清理项，可被 DELETE 注入扩展。'),
('saved_filters', 'TOKEN-EXPIRED-002', 'analyst', '分析师手动登记的清理任务。'),
('audit_logs',    'TOKEN-FLAG-DELETE', 'system',  'FLAG{sqli_delete_extra_rows}');
ALTER TABLE cleanup_jobs AUTO_INCREMENT = 1;
