CREATE DATABASE IF NOT EXISTS healthcare_db;
USE healthcare_db;

CREATE TABLE IF NOT EXISTS Medications (
    medication_id   INT AUTO_INCREMENT PRIMARY KEY,
    medication_name VARCHAR(100) NOT NULL UNIQUE
);