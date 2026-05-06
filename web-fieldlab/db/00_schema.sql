CREATE DATABASE IF NOT EXISTS sql_training CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sql_training;

DROP TABLE IF EXISTS saved_filters;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS lab_flags;

CREATE TABLE users (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(120) NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  role VARCHAR(30) NOT NULL,
  department VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
  product_id INT PRIMARY KEY AUTO_INCREMENT,
  sku VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  category VARCHAR(50) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock INT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
  order_id INT PRIMARY KEY AUTO_INCREMENT,
  order_number VARCHAR(30) NOT NULL UNIQUE,
  customer_name VARCHAR(120) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(40) NOT NULL,
  shipping_note VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE support_tickets (
  ticket_id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(120) NOT NULL,
  status VARCHAR(30) NOT NULL,
  owner_email VARCHAR(120) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  internal_note TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
  employee_id INT PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(100) NOT NULL,
  department VARCHAR(50) NOT NULL,
  title VARCHAR(50) NOT NULL,
  badge_code VARCHAR(40) NOT NULL UNIQUE,
  office_city VARCHAR(50) NOT NULL,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE grades (
  grade_id INT PRIMARY KEY AUTO_INCREMENT,
  student_no VARCHAR(20) NOT NULL UNIQUE,
  student_name VARCHAR(80) NOT NULL,
  class_name VARCHAR(50) NOT NULL,
  midterm INT NOT NULL,
  final_exam INT NOT NULL,
  final_score INT NOT NULL,
  teacher_comment VARCHAR(120) NOT NULL DEFAULT '',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
  log_id INT PRIMARY KEY AUTO_INCREMENT,
  actor VARCHAR(80) NOT NULL,
  action VARCHAR(120) NOT NULL,
  action_month CHAR(7) NOT NULL,
  source_ip VARCHAR(45) NOT NULL,
  details TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
  post_id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(120) NOT NULL,
  body TEXT NOT NULL,
  author VARCHAR(80) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comments (
  comment_id INT PRIMARY KEY AUTO_INCREMENT,
  post_id INT NOT NULL,
  commenter VARCHAR(80) NOT NULL,
  body TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_comments_post FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

CREATE TABLE saved_filters (
  filter_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  filter_name VARCHAR(80) NOT NULL,
  department_filter VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_saved_filters_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE lab_flags (
  flag_id INT PRIMARY KEY AUTO_INCREMENT,
  lab_slug VARCHAR(50) NOT NULL UNIQUE,
  flag_value VARCHAR(120) NOT NULL,
  note VARCHAR(255) NOT NULL
);

-- =====================================================================
-- SQLi 扩充关卡（L13-L22）所需的新表
-- =====================================================================

DROP TABLE IF EXISTS register_users;
CREATE TABLE register_users (
  register_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL,
  email VARCHAR(160) NOT NULL,
  role VARCHAR(40) NOT NULL DEFAULT 'guest',
  invite_source VARCHAR(120) NOT NULL DEFAULT 'public',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS cleanup_jobs;
CREATE TABLE cleanup_jobs (
  job_id INT AUTO_INCREMENT PRIMARY KEY,
  target_table VARCHAR(80) NOT NULL,
  expire_token VARCHAR(160) NOT NULL,
  operator VARCHAR(80) NOT NULL,
  note VARCHAR(200) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS audit_access_logs;
CREATE TABLE audit_access_logs (
  access_id INT AUTO_INCREMENT PRIMARY KEY,
  visitor_ua VARCHAR(255) NOT NULL,
  visit_path VARCHAR(255) NOT NULL,
  visit_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS theme_preferences;
CREATE TABLE theme_preferences (
  pref_id INT AUTO_INCREMENT PRIMARY KEY,
  theme_code VARCHAR(60) NOT NULL,
  theme_label VARCHAR(120) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- L17 宽字节注入：使用 GBK 字符集模拟旧系统
DROP TABLE IF EXISTS gbk_legacy_articles;
CREATE TABLE gbk_legacy_articles (
  article_id INT AUTO_INCREMENT PRIMARY KEY,
  keyword VARCHAR(120) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  secret_tag VARCHAR(120) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=gbk COLLATE=gbk_chinese_ci;

DROP TABLE IF EXISTS file_io_attempts;
CREATE TABLE file_io_attempts (
  attempt_id INT AUTO_INCREMENT PRIMARY KEY,
  operation VARCHAR(40) NOT NULL,
  target_path VARCHAR(255) NOT NULL,
  result_brief VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS dnslog_callbacks;
CREATE TABLE dnslog_callbacks (
  callback_id INT AUTO_INCREMENT PRIMARY KEY,
  subdomain VARCHAR(160) NOT NULL,
  decoded_data VARCHAR(255) NOT NULL DEFAULT '',
  received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS nosql_docs;
CREATE TABLE nosql_docs (
  doc_id INT AUTO_INCREMENT PRIMARY KEY,
  collection VARCHAR(60) NOT NULL,
  document_json JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS dialect_samples;
CREATE TABLE dialect_samples (
  sample_id INT AUTO_INCREMENT PRIMARY KEY,
  dialect_name VARCHAR(40) NOT NULL,
  feature VARCHAR(80) NOT NULL,
  sample_payload VARCHAR(255) NOT NULL,
  note VARCHAR(255) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
