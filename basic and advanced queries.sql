
USE healthcare_db;
# 1st Basic Query
SELECT
    mc.condition_name,
    COUNT(a.admission_id)         AS total_admissions,
    ROUND(AVG(a.billing_amount), 2) AS avg_billing_amount,
    ROUND(MIN(a.billing_amount), 2) AS min_billing,
    ROUND(MAX(a.billing_amount), 2) AS max_billing,
    ROUND(SUM(a.billing_amount), 2) AS total_revenue
FROM Admissions a
JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
GROUP BY mc.condition_id, mc.condition_name
ORDER BY avg_billing_amount DESC;
# 2nd Basic Query
SELECT
    TRIM(p.gender)                  AS gender,
    TRIM(p.insurance_provider)      AS insurance_provider,
    COUNT(DISTINCT p.patient_id)    AS patient_count
FROM Patients p
WHERE p.gender IS NOT NULL
GROUP BY TRIM(p.gender), TRIM(p.insurance_provider)
ORDER BY gender, patient_count DESC;
#1 Advanced query
SELECT
    d.doctor_name,
    h.hospital_name,
    ROUND(SUM(a.billing_amount), 2)  AS total_billed,
    COUNT(a.admission_id)            AS num_admissions,
    RANK() OVER (
        PARTITION BY h.hospital_id
        ORDER BY SUM(a.billing_amount) DESC
    )                                AS rank_in_hospital
FROM Admissions a
JOIN Doctors   d ON a.doctor_id   = d.doctor_id
JOIN Hospitals h ON a.hospital_id = h.hospital_id
GROUP BY d.doctor_id, h.hospital_id
ORDER BY h.hospital_name, rank_in_hospital;