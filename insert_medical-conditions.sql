USE healthcare_db;
INSERT INTO Medical_Conditions (condition_name)
SELECT DISTINCT TRIM(raw_condition)
FROM raw_healthcare
WHERE raw_condition IS NOT NULL;
