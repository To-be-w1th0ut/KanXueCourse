USE sql_training;

-- 教学环境：授予 labapp FILE 权限，用于 L19 INTO OUTFILE / LOAD_FILE 演示。
-- 真实生产环境严禁这样做（FILE 是 root-only 高危权限）。
GRANT FILE ON *.* TO 'labapp'@'%';
FLUSH PRIVILEGES;

INSERT INTO users (username, password, display_name, role, department) VALUES
('admin', 'winter2026', 'Zhou Admin', 'administrator', 'Security'),
('teacher', 'classroom123', 'Lin Teacher', 'instructor', 'Education'),
('analyst', 'report!2026', 'Ming Analyst', 'analyst', 'Operations'),
('intern', 'welcome1', 'Tao Intern', 'intern', 'Support');

INSERT INTO products (sku, name, category, price, stock, description) VALUES
('RTR-AX90', 'Router AX90', 'Hardware', 899.00, 12, 'Tri-band wireless router with lab-grade telemetry support.'),
('SW-24P', 'Switch 24P', 'Hardware', 699.00, 9, 'Managed switch for teaching VLAN and access control.'),
('VPN-CLD', 'VPN Cloud Seat', 'Software', 129.00, 300, 'Subscription package used in branch connectivity demonstrations.'),
('WAF-BASIC', 'WAF Basic', 'Security', 399.00, 40, 'Entry-level web application firewall license.'),
('EDR-LAB', 'EDR Lab Agent', 'Security', 219.00, 150, 'Endpoint detection agent bundle for sandbox devices.'),
('CAM-PTZ', 'PTZ Camera Kit', 'Hardware', 459.00, 16, 'Camera kit used in edge security exercises.');

INSERT INTO orders (order_number, customer_name, total_amount, status, shipping_note) VALUES
('SO-2026-0416', 'Acme School', 1280.00, 'Packed', 'Priority shipping requested by lab coordinator.'),
('SO-2026-0417', 'Blue Harbor College', 5499.00, 'Awaiting Payment', 'Finance approval pending.'),
('SO-2026-0418', 'Northwind Training', 399.00, 'Delivered', 'Signed by warehouse desk.'),
('SO-2026-0419', 'Acme School', 9200.00, 'Processing', 'Bundle includes extra spares.'),
('SO-2026-0420', 'Jade River Institute', 240.00, 'Packed', 'Low-value order kept for API demos.');

INSERT INTO support_tickets (title, status, owner_email, severity, internal_note) VALUES
('VPN portal fails after password reset', 'Open', 'ops1@fieldlab.local', 'high', 'Customer insists issue started after LDAP sync.'),
('Audit export misses rows', 'Investigating', 'ops2@fieldlab.local', 'medium', 'Legacy SQL path still enabled for report endpoint.'),
('Training switch port down', 'Closed', 'noc@fieldlab.local', 'low', 'Cable replaced in classroom rack.'),
('CEO demo account locked', 'Open', 'itdesk@fieldlab.local', 'critical', 'Temporary unlock granted for morning rehearsal.');

INSERT INTO employees (full_name, department, title, badge_code, office_city, active) VALUES
('Chen Rui', 'Sales', 'Regional Lead', 'BDG-1142', 'Shanghai', 1),
('Liu Wen', 'Operations', 'Dispatcher', 'BDG-2255', 'Hangzhou', 1),
('Zhao Ning', 'Security', 'SOC Analyst', 'BDG-9011', 'Beijing', 1),
('Sun Qiao', 'Education', 'Lab Instructor', 'BDG-4408', 'Nanjing', 1),
('He Fan', 'Sales', 'Account Manager', 'BDG-1143', 'Shenzhen', 1),
('Gu Kai', 'Finance', 'Controller', 'BDG-7712', 'Suzhou', 0);

INSERT INTO grades (student_no, student_name, class_name, midterm, final_exam, final_score, teacher_comment) VALUES
('S1001', 'Li Jia', 'WebSec-1', 84, 89, 87, '基础扎实'),
('S1002', 'Wang Yue', 'WebSec-1', 78, 92, 86, '实验表现优秀'),
('S1003', 'Zhang Nan', 'WebSec-2', 69, 75, 72, '需要加强 SQL 基础'),
('S1004', 'Xu Han', 'WebSec-2', 88, 94, 91, '课堂互动积极'),
('S1005', 'Qian Mo', 'WebSec-3', 91, 96, 94, '讲题能力强'),
('S1006', 'Deng Yu', 'WebSec-3', 73, 81, 78, '需要更多练习');

INSERT INTO audit_logs (actor, action, action_month, source_ip, details, created_at) VALUES
('teacher', 'export grades summary', '2026-04', '10.10.4.12', 'Monthly export generated for class WebSec-2.', '2026-04-10 09:15:00'),
('analyst', 'download order list', '2026-04', '10.10.4.23', 'Sales pipeline review for top customers.', '2026-04-12 14:22:00'),
('admin', 'rotate temporary passwords', '2026-04', '10.10.1.5', 'Night maintenance window.', '2026-04-15 00:40:00'),
('intern', 'preview support tickets', '2026-03', '10.10.9.77', 'Troubleshooting workshop.', '2026-03-22 16:18:00'),
('teacher', 'export grades summary', '2026-05', '10.10.4.12', 'New cycle export for exam review.', '2026-05-01 08:05:00');

INSERT INTO posts (title, body, author) VALUES
('Classroom Update', 'Week 4 focuses on detection and prevention.', 'Lin Teacher'),
('Operations Memo', 'Remember to reset the practice environment after each demo.', 'Ming Analyst');

INSERT INTO comments (post_id, commenter, body) VALUES
(1, 'Li Jia', '收到，会提前预习参数化查询。'),
(1, 'Zhang Nan', '想看更多关于盲注的练习。'),
(2, 'Wang Yue', '建议把 reset 按钮放到首页。');

INSERT INTO lab_flags (lab_slug, flag_value, note) VALUES
('product-union', 'FLAG{union_makes_data_walk_out}', '用于 UNION 场景演示跨表读取'),
('error-ticket', 'FLAG{verbose_errors_feed_attackers}', '用于报错型注入演示'),
('employee-blind', 'FLAG{boolean_side_channels_still_talk}', '用于布尔盲注演示'),
('shipping-time', 'FLAG{time_is_a_data_channel}', '用于时间盲注演示'),
('api-json-sqli', 'FLAG{json_is_still_just_input}', '用于 API 注入演示'),
('orm-misuse', 'FLAG{orm_is_not_a_magic_shield}', '用于 ORM 误用演示'),
('insert-register', 'FLAG{insert_values_can_be_extended}', '用于 INSERT 注入演示'),
('delete-cleanup', 'FLAG{sqli_delete_extra_rows}', '用于 DELETE 注入演示'),
('header-audit', 'FLAG{header_is_input_too}', '用于 Header 注入演示'),
('cookie-theme', 'FLAG{cookie_sqli_hidden_theme}', '用于 Cookie 注入演示'),
('wide-byte', 'FLAG{wide_byte_addslashes_bypass}', '用于宽字节注入演示'),
('waf-blacklist-bypass', 'FLAG{blacklist_can_always_be_bypassed}', '用于 WAF 黑名单绕过演示'),
('file-rw-outfile', 'FLAG{file_priv_is_dangerous}', '用于文件读写演示'),
('oob-dnslog', 'FLAG{oob_channel_for_blind_injection}', '用于 DNSLog 带外演示'),
('nosql-style', 'FLAG{nosql_ne_bypass_login}', '用于 NoSQL 注入演示'),
('dialect-diff', 'FLAG{dialects_share_the_same_sin}', '用于方言差异演示');

-- =====================================================================
-- SQLi 扩充关卡（L13-L22）的种子数据
-- =====================================================================

INSERT INTO register_users (username, email, role, invite_source) VALUES
('alice', 'alice@class.local', 'student', 'public'),
('bob',   'bob@class.local',   'student', 'public');

INSERT INTO cleanup_jobs (target_table, expire_token, operator, note) VALUES
('audit_logs',    'TOKEN-EXPIRED-001', 'system',  '默认清理项，可被 DELETE 注入扩展。'),
('saved_filters', 'TOKEN-EXPIRED-002', 'analyst', '分析师手动登记的清理任务。'),
('audit_logs',    'TOKEN-FLAG-DELETE', 'system',  'FLAG{sqli_delete_extra_rows}');

INSERT INTO audit_access_logs (visitor_ua, visit_path) VALUES
('Mozilla/5.0 (Macintosh)', '/dashboard'),
('curl/8.4.0',              '/labs');

INSERT INTO theme_preferences (theme_code, theme_label, is_active) VALUES
('aurora', '极光主题',                              1),
('amber',  '琥珀主题',                              1),
('hidden', 'FLAG{cookie_sqli_hidden_theme}',       0);

INSERT INTO gbk_legacy_articles (keyword, title, body, secret_tag) VALUES
('welcome',   '旧版宽字节系统欢迎语', '本系统沿用 GBK 编码，请使用经典浏览器访问。', ''),
('changelog', '版本更新记录',         '2008 年起未再升级。',                          'FLAG{wide_byte_addslashes_bypass}');

INSERT INTO nosql_docs (collection, document_json) VALUES
('users',  '{"username":"admin","password":"super-secret","role":"admin","note":"FLAG{nosql_ne_bypass_login}"}'),
('users',  '{"username":"alice","password":"alice123","role":"student"}'),
('orders', '{"order_no":"O-9001","amount":299,"customer":"alice"}');

INSERT INTO dialect_samples (dialect_name, feature, sample_payload, note) VALUES
('MySQL',      'sleep',            'SELECT SLEEP(2)',                'MySQL/MariaDB 通用'),
('MySQL',      'concat',           'CONCAT(a, b)',                   ''),
('PostgreSQL', 'sleep',            'SELECT pg_sleep(2)',             'PG 专用'),
('PostgreSQL', 'concat',           'a || b',                         '字符串拼接'),
('SQL Server', 'sleep',            "WAITFOR DELAY '0:0:2'",          'MSSQL 专用'),
('SQL Server', 'cmd',              'EXEC xp_cmdshell ''dir''',       '高权限可 RCE'),
('Oracle',     'sleep',            'DBMS_PIPE.RECEIVE_MESSAGE(...)', '不易被发现'),
('SQLite',     'sleep_workaround', 'SELECT randomblob(1e9)',         'SQLite 无 sleep，用计算消耗时间');
