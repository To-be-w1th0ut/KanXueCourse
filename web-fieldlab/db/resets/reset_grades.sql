USE sql_training;
DELETE FROM grades;
INSERT INTO grades (student_no, student_name, class_name, midterm, final_exam, final_score, teacher_comment) VALUES
('S1001', 'Li Jia', 'WebSec-1', 84, 89, 87, '基础扎实'),
('S1002', 'Wang Yue', 'WebSec-1', 78, 92, 86, '实验表现优秀'),
('S1003', 'Zhang Nan', 'WebSec-2', 69, 75, 72, '需要加强 SQL 基础'),
('S1004', 'Xu Han', 'WebSec-2', 88, 94, 91, '课堂互动积极'),
('S1005', 'Qian Mo', 'WebSec-3', 91, 96, 94, '讲题能力强'),
('S1006', 'Deng Yu', 'WebSec-3', 73, 81, 78, '需要更多练习');
ALTER TABLE grades AUTO_INCREMENT = 1;
