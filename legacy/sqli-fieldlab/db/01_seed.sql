USE sql_training;

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
('orm-misuse', 'FLAG{orm_is_not_a_magic_shield}', '用于 ORM 误用演示');
