SELECT blood_type, 
       ROUND(AVG(age), 1) AS avg_age,
       COUNT(*) AS total_patients
FROM Patients
GROUP BY blood_type
ORDER BY avg_age DESC;