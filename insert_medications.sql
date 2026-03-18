USE healthcare_db;
INSERT INTO Medications (medication_name)
SELECT DISTINCT TRIM(raw_medication)
FROM raw_healthcare
WHERE raw_medication IS NOT NULL;