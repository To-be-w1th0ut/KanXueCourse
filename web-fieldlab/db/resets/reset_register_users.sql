USE sql_training;
DELETE FROM register_users;
INSERT INTO register_users (username, email, role, invite_source) VALUES
('alice', 'alice@class.local', 'student', 'public'),
('bob',   'bob@class.local',   'student', 'public');
ALTER TABLE register_users AUTO_INCREMENT = 1;
