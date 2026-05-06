USE sql_training;
DELETE FROM audit_access_logs;
INSERT INTO audit_access_logs (visitor_ua, visit_path) VALUES
('Mozilla/5.0 (Macintosh)', '/dashboard'),
('curl/8.4.0',              '/labs');
ALTER TABLE audit_access_logs AUTO_INCREMENT = 1;
