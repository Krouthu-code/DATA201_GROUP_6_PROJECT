CREATE DATABASE IF NOT EXISTS healthcare_db;
USE healthcare_db;

CREATE TABLE IF NOT EXISTS Patients (
    patient_id         INT AUTO_INCREMENT PRIMARY KEY,
    full_name          VARCHAR(100),
    age                INT,
    gender             VARCHAR(10),
    blood_type         VARCHAR(3),
    insurance_provider VARCHAR(50)
);