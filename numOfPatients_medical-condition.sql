SELECT mc.condition_name,
       COUNT(*) AS total_patients
FROM Admissions a
JOIN Medical_Conditions mc
    ON a.condition_id = mc.condition_id
GROUP BY mc.condition_name
ORDER BY total_patients DESC;