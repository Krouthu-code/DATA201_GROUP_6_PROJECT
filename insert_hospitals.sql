USE healthcare_db;
INSERT INTO Hospitals (hospital_name)
SELECT DISTINCT TRIM(raw_hospital)
FROM raw_healthcare
WHERE raw_hospital IS NOT NULL;