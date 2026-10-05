
CREATE OR REPLACE DATABASE db;
USE db;

CREATE TABLE user3 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    email VARCHAR(50),
    password VARCHAR(255)  -- increased length for hashed password
);
