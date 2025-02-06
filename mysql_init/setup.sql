-- Create a database named "idea_bank"
CREATE DATABASE idea_bank;

-- Use the idea_bank database
USE idea_bank;

-- Create the "all_report" form, which records all weekly report information
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

-- Create the "website_link" form that stores all the news information crawled from the website
CREATE TABLE IF NOT EXISTS `website_link` (
	`id` INT AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `url` VARCHAR(200) NOT NULL,
    `source` VARCHAR(100) NOT NULL,
    `time` DATETIME NOT NULL,
    PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create the "user" form, which stores user information
CREATE TABLE IF NOT EXISTS `user` (
	`user_id` INT AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `nickname` VARCHAR(50) NOT NULL,
    `password` CHAR(32),
    `avatar` VARCHAR(50) NOT NULL DEFAULT 'default.png',
    `email` VARCHAR(50),
    `role` VARCHAR(10) NOT NULL DEFAULT 'user', 
	 PRIMARY KEY (`user_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
