USE sql_training;
DELETE FROM theme_preferences;
INSERT INTO theme_preferences (theme_code, theme_label, is_active) VALUES
('aurora', '极光主题',                              1),
('amber',  '琥珀主题',                              1),
('hidden', 'FLAG{cookie_sqli_hidden_theme}',       0);
ALTER TABLE theme_preferences AUTO_INCREMENT = 1;
