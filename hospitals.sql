CREATE DATABASE IF NOT EXISTS healthcare_db;

USE healthcare_db;

CREATE TABLE IF NOT EXISTS Hospitals (
    hospital_id   INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name VARCHAR(150) NOT NULL UNIQUE
);