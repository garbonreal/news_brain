# 创建命名为“idea_bank”的数据库
CREATE DATABASE idea_bank;

# 使用“idea_bank”数据库
USE idea_bank;

# 创建“all_report”表单，该表记录了所有周报的信息
CREATE TABLE IF NOT EXISTS all_report (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(100) NOT NULL,
    `create_time` DATETIME NOT NULL,
    `principal` VARCHAR(20) NOT NULL,
    `news_count` INT NOT NULL,
    `weekly_report_count` INT NOT NULL,
    `is_publish` VARCHAR(20) NOT NULL,
    `is_edit` VARCHAR(20) NOT NULL,
    `content_title` VARCHAR(100),
    `content` TEXT,
    `weekly_report_name` VARCHAR(100),
    `start_time` DATETIME,
    `end_time` DATETIME,
    `search_key` VARCHAR(100),
    `filter_key` VARCHAR(100),
    `curr_page` INT,
    `page_count` INT,
    `length` INT,
    `first_filter_length` INT
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# 创建“website_link”，该表单存储了从网站上爬取的所有新闻信息
CREATE TABLE IF NOT EXISTS `website_link` (
	`id` INT AUTO_INCREMENT,
    `title` VARCHAR(100) NOT NULL,
    `url` VARCHAR(100) NOT NULL,
    `source` VARCHAR(100) NOT NULL,
    `time` DATETIME NOT NULL,
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# 创建“user”，该表单存储了用户信息
CREATE TABLE IF NOT EXISTS `user` (
	`user_id` INT AUTO_INCREMENT,  -- 用户唯一id
    `username` VARCHAR(50) NOT NULL,  -- 用户登录时输入账号
    `nickname` VARCHAR(50) NOT NULL,  --	用户昵称
    `password` CHAR(32), -- MD5加密字符 用户登录密码
    `avatar` VARCHAR(50) NOT NULL DEFAULT 'default.png',  -- 有默认头像 头像文件名称
    `email` VARCHAR(50),  -- 用户安全邮箱
    `role` VARCHAR(10) NOT NULL DEFAULT 'user',  -- admin为管理员 user为普通用户 用户身份
	 PRIMARY KEY (`user_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
