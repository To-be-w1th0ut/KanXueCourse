USE sql_training;
DELETE FROM dnslog_callbacks;
DELETE FROM file_io_attempts;
ALTER TABLE dnslog_callbacks AUTO_INCREMENT = 1;
ALTER TABLE file_io_attempts AUTO_INCREMENT = 1;
