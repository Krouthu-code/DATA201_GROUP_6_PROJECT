SELECT h.hospital_name,
       ROUND(AVG(a.billing_amount), 2) AS avg_billing
FROM Admissions a
JOIN Hospitals h
    ON a.hospital_id = h.hospital_id
GROUP BY h.hospital_name
ORDER BY avg_billing DESC
LIMIT 10;