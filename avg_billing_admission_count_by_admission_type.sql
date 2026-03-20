SELECT admission_type,
       COUNT(admission_id) AS total_admissions,
       ROUND(AVG(billing_amount), 2) AS avg_billing
FROM Admissions
GROUP BY admission_type
ORDER BY total_admissions DESC;