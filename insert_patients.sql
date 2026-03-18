USE healthcare_db;
INSERT INTO Patients (full_name, age, gender, blood_type, insurance_provider)
SELECT DISTINCT raw_name, raw_age, raw_gender, raw_blood_type, raw_insurance
FROM raw_healthcare
WHERE raw_name IS NOT NULL;