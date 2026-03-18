USE healthcare_db;
INSERT INTO Doctors (doctor_name, hospital_id)
SELECT DISTINCT r.raw_doctor, h.hospital_id
FROM raw_healthcare r
JOIN Hospitals h ON TRIM(r.raw_hospital) = h.hospital_name
WHERE r.raw_doctor IS NOT NULL;