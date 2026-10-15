-- Guest user: portal -> project module only (chat / parse)
-- password: 123456 (same BCrypt as demo users)

INSERT INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
SELECT 110, '??', 'guest', 9, '1', 1, 1, '0', '0', 'admin', sysdate(), 'guest: project view only'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_role WHERE role_id = 110 OR role_key = 'guest');

INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password, status, del_flag, login_ip, login_date, create_by, create_time, remark)
SELECT 110, 103, 'guest', '??', '00', 'guest@project.local', '13800000110', '0', '',
       '$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2',
       '0', '0', '', NULL, 'admin', sysdate(), 'guest demo account'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE user_id = 110 OR user_name = 'guest');

INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES (110, 110);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(110, 2100), (110, 2101), (110, 2102);
