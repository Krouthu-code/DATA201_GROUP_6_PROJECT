use healthcare_db;
SELECT 
    insurance_provider,
    condition_name,
    total_count
FROM (
    SELECT 
        p.insurance_provider,
        mc.condition_name,
        COUNT(*) AS total_count,
        RANK() OVER (
            PARTITION BY p.insurance_provider
            ORDER BY COUNT(*) DESC
        ) AS rnk
    FROM Admissions a
    JOIN Patients p ON a.patient_id = p.patient_id
    JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
    GROUP BY p.insurance_provider, mc.condition_name
) ranked
WHERE rnk <= 3
ORDER BY insurance_provider, rnk;

