SELECT *
FROM (
    SELECT h.hospital_name,
           mc.condition_name,
           ROUND(AVG(a.billing_amount), 2) AS avg_billing,
           RANK() OVER (
               PARTITION BY h.hospital_id
               ORDER BY AVG(a.billing_amount) DESC
           ) AS rank_in_hospital
    FROM Admissions a
    JOIN Hospitals h
        ON a.hospital_id = h.hospital_id
    JOIN Medical_Conditions mc
        ON a.condition_id = mc.condition_id
    GROUP BY h.hospital_name, mc.condition_name, h.hospital_id
) ranked
WHERE rank_in_hospital <= 3;