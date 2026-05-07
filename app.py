from flask import Flask, render_template, jsonify
import mysql.connector

app = Flask(__name__)

# ─── DB CONFIG ────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",   # change this
    "database": "healthcare_db"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def run_query(sql):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# ══════════════════════════════════════════════════════════════
#  QUERIES
#  Each query has an "author" field matching a team member name.
#  To add your queries: copy a block below, change "author" to
#  your name, add your SQL and chart config.
# ══════════════════════════════════════════════════════════════

QUERIES = {

    # ── KARISHMA ──────────────────────────────────────────────

    "billing_by_condition": {
        "author": "Karishma",
        "title": "Avg Billing by Medical Condition",
        "chart": "bar",
        "x": "condition_name",
        "y": "avg_billing",
        "color": "#14b8a6",
        "sql": """
            SELECT mc.condition_name,
                   ROUND(AVG(a.billing_amount), 2) AS avg_billing,
                   COUNT(*)                        AS total_admissions
            FROM   Admissions a
            JOIN   Medical_Conditions mc ON a.condition_id = mc.condition_id
            GROUP  BY mc.condition_name
            ORDER  BY avg_billing DESC
        """
    },

    "avg_age_by_blood_type": {
        "author": "Karishma",
        "title": "Average Patient Age by Blood Type",
        "chart": "bar",
        "x": "blood_type",
        "y": "avg_age",
        "color": "#f59e0b",
        "sql": """
            SELECT blood_type,
                   ROUND(AVG(age), 1) AS avg_age
            FROM   Patients
            GROUP  BY blood_type
            ORDER  BY avg_age DESC
        """
    },

    "monthly_admissions_trend": {
        "author": "Karishma",
        "title": "Monthly Admissions Trend",
        "chart": "line",
        "x": "month",
        "y": "admissions",
        "color": "#3b82f6",
        "sql": """
            SELECT DATE_FORMAT(date_of_admission, '%Y-%m') AS month,
                   COUNT(*)                                AS admissions,
                   ROUND(AVG(billing_amount), 2)           AS avg_billing
            FROM   Admissions
            GROUP  BY month
            ORDER  BY month ASC
        """
    },

    "top_conditions_by_insurer": {
        "author": "Karishma",
        "title": "Top 3 Conditions per Insurance Provider",
        "chart": "grouped_bar",
        "x": "insurance_provider",
        "y": "total_count",
        "group": "condition_name",
        "sql": """
            SELECT insurance_provider, condition_name, total_count
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
            ORDER BY insurance_provider, rnk
        """
    },

    "high_value_patients_cte": {
        "author": "Karishma",
        "title": "High-Value Patients vs Average (CTE)",
        "chart": "bar",
        "x": "blood_type",
        "y": "high_value_patients",
        "color": "#a855f7",
        "sql": """
            WITH patient_totals AS (
                SELECT a.patient_id,
                       SUM(a.billing_amount) AS lifetime_billing
                FROM Admissions a
                GROUP BY a.patient_id
            ),
            avg_billing AS (
                SELECT AVG(lifetime_billing) AS overall_avg
                FROM patient_totals
            )
            SELECT
                p.blood_type,
                COUNT(*) AS high_value_patients,
                ROUND(AVG(pt.lifetime_billing), 2) AS avg_lifetime_billing
            FROM patient_totals pt
            JOIN Patients p ON pt.patient_id = p.patient_id
            CROSS JOIN avg_billing ab
            WHERE pt.lifetime_billing > ab.overall_avg
            GROUP BY p.blood_type
            ORDER BY high_value_patients DESC
        """
    },

    "billing_percentile_by_condition": {
        "author": "Karishma",
        "title": "Avg Billing by Condition with Running Total (Window Function)",
        "chart": "bar",
        "x": "condition_name",
        "y": "avg_billing",
        "color": "#ec4899",
        "sql": """
            SELECT
                condition_name,
                avg_billing,
                min_billing,
                max_billing,
                total_cases,
                ROUND(SUM(avg_billing) OVER (
                    ORDER BY avg_billing DESC
                    ROWS UNBOUNDED PRECEDING
                ), 2) AS running_total
            FROM (
                SELECT
                    mc.condition_name,
                    ROUND(AVG(a.billing_amount), 2) AS avg_billing,
                    ROUND(MIN(a.billing_amount), 2) AS min_billing,
                    ROUND(MAX(a.billing_amount), 2) AS max_billing,
                    COUNT(*)                        AS total_cases
                FROM Admissions a
                JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
                GROUP BY mc.condition_name
            ) aggregated
            ORDER BY avg_billing DESC
        """
    },

    "readmission_risk_subquery": {
        "author": "Karishma",
        "title": "Patients with Multiple Admissions (Subquery)",
        "chart": "bar",
        "x": "admission_count",
        "y": "patient_count",
        "color": "#f97316",
        "sql": """
            SELECT
                admission_count,
                COUNT(*) AS patient_count,
                ROUND(AVG(avg_billing), 2) AS avg_billing_per_visit
            FROM (
                SELECT
                    a.patient_id,
                    COUNT(*) AS admission_count,
                    AVG(a.billing_amount) AS avg_billing
                FROM Admissions a
                GROUP BY a.patient_id
                HAVING COUNT(*) > 1
            ) multi_admit
            GROUP BY admission_count
            ORDER BY admission_count ASC
        """
    },

    "condition_admission_rolling": {
        "author": "Karishma",
        "title": "Rolling 3-Month Avg Admissions by Condition (CTE + Window)",
        "chart": "line",
        "x": "month",
        "y": "rolling_avg",
        "group": "condition_name",
        "color": "#06b6d4",
        "sql": """
            WITH monthly_counts AS (
                SELECT
                    DATE_FORMAT(a.date_of_admission, '%Y-%m') AS month,
                    mc.condition_name,
                    COUNT(*) AS admissions
                FROM Admissions a
                JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
                GROUP BY month, mc.condition_name
            ),
            ranked AS (
                SELECT
                    month,
                    condition_name,
                    admissions,
                    ROUND(AVG(admissions) OVER (
                        PARTITION BY condition_name
                        ORDER BY month
                        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                    ), 1) AS rolling_avg,
                    ROW_NUMBER() OVER (
                        PARTITION BY condition_name ORDER BY month
                    ) AS rn
                FROM monthly_counts
            )
            SELECT month, condition_name, admissions, rolling_avg
            FROM ranked
            WHERE rn >= 3
            ORDER BY condition_name, month
        """
    },

    # ── CHINMAYI ──────────────────────────────────────────────

    "chinmayi_patient_insurance_demographics": {
        "author": "Chinmayi",
        "title": "Patient Distribution by Gender and Insurance",
        "chart": "bar",
        "x": "insurance_provider",
        "y": "patient_count",
        "color": "#10b981", 
        "sql": """
            SELECT
                TRIM(p.gender)                  AS gender,
                TRIM(p.insurance_provider)      AS insurance_provider,
                COUNT(DISTINCT p.patient_id)    AS patient_count
            FROM Patients p
            WHERE p.gender IS NOT NULL
            GROUP BY TRIM(p.gender), TRIM(p.insurance_provider)
            ORDER BY gender, patient_count DESC
        """
    },

"chinmayi_doctor_hospital_ranking": {
        "author": "Chinmayi",
        "title": "Doctor Billing Rank by Hospital",
        "chart": "bar",
        "x": "doctor_name",
        "y": "total_billed",
        "color": "#f59e0b",
        "sql": """
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
            ORDER BY h.hospital_name, rank_in_hospital
        """
    },
"chinmayi_condition_financial_summary": {
        "author": "Chinmayi",
        "title": "Medical Condition Financial Performance",
        "chart": "bar",
        "x": "condition_name",
        "y": "total_revenue",
        "color": "#3b82f6", 
        "sql": """
            SELECT
                mc.condition_name,
                COUNT(a.admission_id)           AS total_admissions,
                ROUND(AVG(a.billing_amount), 2) AS avg_billing_amount,
                ROUND(MIN(a.billing_amount), 2) AS min_billing,
                ROUND(MAX(a.billing_amount), 2) AS max_billing,
                ROUND(SUM(a.billing_amount), 2) AS total_revenue
            FROM Admissions a
            JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
            GROUP BY mc.condition_id, mc.condition_name
            ORDER BY avg_billing_amount DESC
        """
    },

    "chinmayi_condition_billing_ranked": {
        "author": "Chinmayi",
        "title": "Medical Condition Billing Rank (Window Function)",
        "chart": "bar",
        "x": "condition_name",
        "y": "avg_billing",
        "color": "#6366f1",
        "sql": """
            SELECT
                condition_name,
                avg_billing,
                billing_rank
            FROM (
                SELECT
                    mc.condition_name,
                    ROUND(AVG(a.billing_amount), 2) AS avg_billing,
                    RANK() OVER (
                        ORDER BY AVG(a.billing_amount) DESC
                    ) AS billing_rank
                FROM   Admissions a
                JOIN   Medical_Conditions mc ON a.condition_id = mc.condition_id
                GROUP  BY mc.condition_name
            ) ranked
            ORDER BY billing_rank ASC
        """
    },

    "chinmayi_high_risk_above_hospital_avg": {
        "author": "Chinmayi",
        "title": "Patients Billed 50% Above Their Hospital Average (CTE)",
        "chart": "bar",
        "x": "hospital",
        "y": "high_risk_count",
        "color": "#ef4444",
        "sql": """
            WITH hospital_avg AS (
                SELECT h.hospital_name AS hospital,
                       ROUND(AVG(a.billing_amount), 2) AS avg_billing
                FROM   Admissions a
                JOIN   hospitals h ON a.hospital_id = h.hospital_id
                GROUP  BY h.hospital_name
            )
            SELECT ha.hospital,
                   COUNT(*) AS high_risk_count,
                   ROUND(AVG(a.billing_amount), 2) AS avg_high_risk_billing,
                   ha.avg_billing AS hospital_avg_billing
            FROM   Admissions a
            JOIN   hospitals h ON a.hospital_id = h.hospital_id
            JOIN   hospital_avg ha ON h.hospital_name = ha.hospital
            WHERE  a.billing_amount > ha.avg_billing * 1.5
            GROUP  BY ha.hospital, ha.avg_billing
            ORDER  BY high_risk_count DESC
        """
    },

    "chinmayi_readmission_by_condition": {
        "author": "Chinmayi",
        "title": "Readmission Count by Condition (Subquery + HAVING)",
        "chart": "horizontal_bar",
        "y": "condition_name",
        "x": "readmission_count",
        "color": "#f59e0b",
        "sql": """
            SELECT
                mc.condition_name,
                COUNT(*) AS readmission_count
            FROM (
                SELECT
                    a.patient_id,
                    a.condition_id,
                    COUNT(*) AS visit_count
                FROM   Admissions a
                GROUP  BY a.patient_id, a.condition_id
                HAVING COUNT(*) > 1
            ) AS repeat_patients
            JOIN Medical_Conditions mc ON repeat_patients.condition_id = mc.condition_id
            GROUP  BY mc.condition_name
            ORDER  BY readmission_count DESC
        """
    },

    "chinmayi_billing_percentile_ntile": {
        "author": "Chinmayi",
        "title": "Patient Billing Quartile Distribution (NTILE Window Function)",
        "chart": "bar",
        "x": "billing_quartile",
        "y": "patient_count",
        "color": "#10b981",
        "sql": """
            SELECT
                billing_quartile,
                COUNT(*)                        AS patient_count,
                ROUND(MIN(billing_amount), 2)   AS min_billing,
                ROUND(MAX(billing_amount), 2)   AS max_billing,
                ROUND(AVG(billing_amount), 2)   AS avg_billing
            FROM (
                SELECT
                    patient_id,
                    billing_amount,
                    CONCAT('Q', NTILE(4) OVER (
                        ORDER BY billing_amount ASC
                    )) AS billing_quartile
                FROM Admissions
            ) AS quartiled
            GROUP  BY billing_quartile
            ORDER  BY billing_quartile ASC
        """
    },

    "chinmayi_doctor_condition_volume": {
        "author": "Chinmayi",
        "title": "Top Doctors by Condition Volume (Subquery + Rank)",
        "chart": "bar",
        "x": "doctor_name",
        "y": "total_patients",
        "color": "#8b5cf6",
        "sql": """
            SELECT
                doctor_name,
                condition_name,
                total_patients,
                avg_billing
            FROM (
                SELECT
                    d.doctor_name,
                    mc.condition_name,
                    COUNT(*)                        AS total_patients,
                    ROUND(AVG(a.billing_amount), 2) AS avg_billing,
                    RANK() OVER (
                        PARTITION BY mc.condition_name
                        ORDER BY COUNT(*) DESC
                    ) AS rnk
                FROM   Admissions a
                JOIN   Medical_Conditions mc ON a.condition_id = mc.condition_id
                JOIN   Doctors d ON a.doctor_id = d.doctor_id
                GROUP  BY d.doctor_name, mc.condition_name
            ) ranked
            WHERE  rnk = 1
            ORDER  BY total_patients DESC
        """
    },

    # ── MANSI ─────────────────────────────────────────────────

   "mansi_admission_day_distribution": {
    "author": "Mansi",
    "title": "Admissions by Day of Week",
    "chart": "bar",
    "x": "admission_day",
    "y": "total_admissions",
    "color": "#10b981",
    "sql": """
        SELECT
            DAYNAME(date_of_admission) AS admission_day,
            COUNT(*) AS total_admissions
        FROM Admissions
        GROUP BY DAYOFWEEK(date_of_admission), DAYNAME(date_of_admission)
        ORDER BY DAYOFWEEK(date_of_admission)
    """
},

"mansi_weekday_vs_weekend": {
    "author": "Mansi",
    "title": "Weekday vs Weekend Admissions",
    "chart": "pie",
    "x": "admission_day_type",
    "y": "total_admissions",
    "color": "#3b82f6",
    "sql": """
        SELECT
            CASE
                WHEN DAYOFWEEK(date_of_admission) IN (1,7)
                THEN 'Weekend'
                ELSE 'Weekday'
            END AS admission_day_type,
            COUNT(*) AS total_admissions
        FROM Admissions
        GROUP BY admission_day_type
    """
},

    "mansi_hospital_billing_rank_window": {
        "author": "Mansi",
        "title": "Hospital Billing Rank",
        "chart": "bar",
        "x": "hospital",
        "y": "avg_billing",
        "color": "#f97316",
        "sql": """
            SELECT hospital_name AS hospital,
                   avg_billing,
                   RANK() OVER (ORDER BY avg_billing DESC) AS billing_rank
            FROM (
                SELECT h.hospital_name,
                       ROUND(AVG(a.billing_amount), 2) AS avg_billing
                FROM Admissions a
                JOIN hospitals h ON a.hospital_id = h.hospital_id
                GROUP BY h.hospital_name
            ) hospital_summary
            ORDER BY billing_rank ASC
        """
    },

    "mansi_high_cost_admissions_cte": {
        "author": "Mansi",
        "title": "High Cost Admissions by Admission Type",
        "chart": "bar",
        "x": "admission_type",
        "y": "high_cost_count",
        "color": "#dc2626",
        "sql": """
            WITH overall_avg AS (
                SELECT AVG(billing_amount) AS avg_billing
                FROM Admissions
            )
            SELECT a.admission_type,
                   COUNT(*) AS high_cost_count,
                   ROUND(AVG(a.billing_amount), 2) AS avg_high_cost_billing
            FROM Admissions a
            CROSS JOIN overall_avg oa
            WHERE a.billing_amount > oa.avg_billing
            GROUP BY a.admission_type
            ORDER BY high_cost_count DESC
        """
    },

    "mansi_hospital_billing_above_average_cte": {
        "author": "Mansi",
        "title": "Hospitals Above Overall Average Billing",
        "chart": "bar",
        "x": "hospital",
        "y": "avg_billing",
        "color": "#6366f1",
        "sql": """
            WITH overall_avg AS (
                SELECT AVG(billing_amount) AS overall_billing_avg
                FROM Admissions
            )
            SELECT h.hospital_name AS hospital,
                   ROUND(AVG(a.billing_amount), 2) AS avg_billing,
                   COUNT(*) AS total_admissions
            FROM Admissions a
            JOIN hospitals h ON a.hospital_id = h.hospital_id
            GROUP BY h.hospital_name
            HAVING AVG(a.billing_amount) > (SELECT overall_billing_avg FROM overall_avg)
            ORDER BY avg_billing DESC
        """
    },

 "mansi_discharge_month_distribution": {
    "author": "Mansi",
    "title": "Discharge Month Distribution",
    "chart": "bar",
    "x": "discharge_month",
    "y": "total_discharges",
    "color": "#f97316",
    "sql": """
        SELECT
            MONTHNAME(discharge_date) AS discharge_month,
            COUNT(*) AS total_discharges
        FROM Admissions
        GROUP BY MONTH(discharge_date), MONTHNAME(discharge_date)
        ORDER BY MONTH(discharge_date)
    """
},

"mansi_room_usage_by_hospital": {
    "author": "Mansi",
    "title": "Room Usage by Hospital",
    "chart": "bar",
    "x": "hospital_name",
    "y": "rooms_used",
    "color": "#8b5cf6",
    "sql": """
        SELECT
            h.hospital_name,
            COUNT(DISTINCT a.room_number) AS rooms_used
        FROM Admissions a
        JOIN Hospitals h
        ON a.hospital_id = h.hospital_id
        GROUP BY h.hospital_name
        ORDER BY rooms_used DESC
    """
},

    "mansi_hospital_length_of_stay_rank": {
        "author": "Mansi",
        "title": "Hospital Length of Stay Rank",
        "chart": "bar",
        "x": "hospital",
        "y": "avg_days",
        "color": "#8b5cf6",
        "sql": """
            SELECT hospital_name AS hospital,
                   avg_days,
                   RANK() OVER (ORDER BY avg_days DESC) AS stay_rank
            FROM (
                SELECT h.hospital_name,
                       ROUND(AVG(DATEDIFF(a.discharge_date, a.date_of_admission)), 2) AS avg_days
                FROM Admissions a
                JOIN hospitals h ON a.hospital_id = h.hospital_id
                GROUP BY h.hospital_name
            ) stay_summary
            ORDER BY stay_rank
        """
    },

    "mansi_billing_by_room_number": {
    "author": "Mansi",
    "title": "Billing by Room Number",
    "chart": "bar",
    "x": "room_number",
    "y": "avg_billing",
    "color": "#14b8a6",
    "sql": """
        SELECT
            room_number,
            ROUND(AVG(billing_amount), 2) AS avg_billing,
            COUNT(*) AS total_admissions
        FROM Admissions
        GROUP BY room_number
        ORDER BY avg_billing DESC
        LIMIT 10
    """
},

    # ── ABHIJITH ──────────────────────────────────────────────

    "abhijith_basic_emergency_by_gender": {
        "author": "Abhijith",
        "title": "Emergency Admissions by Gender",
        "chart": "bar",
        "x": "gender",
        "y": "emergency_admissions",
        "color": "#2563eb",
        "sql": """
            SELECT p.gender,
                   COUNT(*) AS emergency_admissions
            FROM Admissions a
            JOIN Patients p ON a.patient_id = p.patient_id
            WHERE a.admission_type = 'Emergency'
            GROUP BY p.gender
            ORDER BY emergency_admissions DESC
        """
    },

    "abhijith_basic_medication_usage": {
        "author": "Abhijith",
        "title": "Medication Usage Count",
        "chart": "bar",
        "x": "medication",
        "y": "usage_count",
        "color": "#16a34a",
        "sql": """
            SELECT m.medication_name AS medication,
                   COUNT(*) AS usage_count
            FROM Admissions a
            JOIN Medications m ON a.medication_id = m.medication_id
            GROUP BY m.medication_name
            ORDER BY usage_count DESC
        """
    },

    "abhijith_basic_test_results_by_admission": {
        "author": "Abhijith",
        "title": "Test Results by Admission Type",
        "chart": "grouped_bar",
        "x": "admission_type",
        "y": "total_cases",
        "group": "test_results",
        "sql": """
            SELECT admission_type,
                   test_results,
                   COUNT(*) AS total_cases
            FROM Admissions
            GROUP BY admission_type, test_results
            ORDER BY admission_type, total_cases DESC
        """
    },

    "abhijith_adv_length_of_stay_by_condition": {
        "author": "Abhijith",
        "title": "Average Length of Stay by Condition",
        "chart": "bar",
        "x": "condition_name",
        "y": "avg_stay_days",
        "color": "#9333ea",
        "sql": """
            SELECT mc.condition_name,
                   COUNT(*) AS total_cases,
                   ROUND(AVG(DATEDIFF(a.discharge_date, a.date_of_admission)), 2) AS avg_stay_days
            FROM Admissions a
            JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
            GROUP BY mc.condition_name
            HAVING COUNT(*) >= 5
            ORDER BY avg_stay_days DESC
        """
    },

    "abhijith_adv_billing_lag_by_month": {
        "author": "Abhijith",
        "title": "Monthly Billing Change Using LAG",
        "chart": "line",
        "x": "month",
        "y": "avg_billing",
        "color": "#0284c7",
        "sql": """
            WITH monthly_billing AS (
                SELECT DATE_FORMAT(date_of_admission, '%Y-%m') AS month,
                       ROUND(AVG(billing_amount), 2) AS avg_billing
                FROM Admissions
                GROUP BY month
            )
            SELECT month,
                   avg_billing,
                   LAG(avg_billing) OVER (ORDER BY month) AS previous_month_billing,
                   ROUND(avg_billing - LAG(avg_billing) OVER (ORDER BY month), 2) AS billing_change
            FROM monthly_billing
            ORDER BY month
        """
    },

    "abhijith_adv_top_hospital_per_condition": {
        "author": "Abhijith",
        "title": "Top Hospital per Medical Condition",
        "chart": "bar",
        "x": "condition_name",
        "y": "total_cases",
        "color": "#ea580c",
        "sql": """
            SELECT condition_name,
                   hospital,
                   total_cases
            FROM (
                SELECT mc.condition_name,
                       h.hospital_name AS hospital,
                       COUNT(*) AS total_cases,
                       RANK() OVER (
                           PARTITION BY mc.condition_name
                           ORDER BY COUNT(*) DESC
                       ) AS hospital_rank
                FROM Admissions a
                JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
                JOIN hospitals h ON a.hospital_id = h.hospital_id
                GROUP BY mc.condition_name, h.hospital_name
            ) ranked
            WHERE hospital_rank = 1
            ORDER BY total_cases DESC
        """
    },

    "abhijith_adv_abnormal_results_above_avg": {
    "author": "Abhijith",
    "title": "Test Result Distribution by Condition",
    "chart": "grouped_bar",
    "x": "condition_name",
    "y": "result_count",
    "group": "test_results",
    "color": "#dc2626",
    "sql": """
        SELECT mc.condition_name,
               a.test_results,
               COUNT(*) AS result_count
        FROM Admissions a
        JOIN Medical_Conditions mc ON a.condition_id = mc.condition_id
        GROUP BY mc.condition_name, a.test_results
        ORDER BY mc.condition_name, result_count DESC
    """
    },

    "abhijith_adv_patient_age_billing_category": {
        "author": "Abhijith",
        "title": "Billing by Patient Age Group",
        "chart": "bar",
        "x": "age_group",
        "y": "avg_billing",
        "color": "#0891b2",
        "sql": """
            SELECT age_group,
                   COUNT(*) AS total_admissions,
                   ROUND(AVG(billing_amount), 2) AS avg_billing
            FROM (
                SELECT a.billing_amount,
                       CASE
                           WHEN p.age < 18 THEN 'Under 18'
                           WHEN p.age BETWEEN 18 AND 35 THEN '18-35'
                           WHEN p.age BETWEEN 36 AND 55 THEN '36-55'
                           WHEN p.age BETWEEN 56 AND 75 THEN '56-75'
                           ELSE '76+'
                       END AS age_group
                FROM Admissions a
                JOIN Patients p ON a.patient_id = p.patient_id
            ) age_summary
            GROUP BY age_group
            ORDER BY avg_billing DESC
        """
    },

}

# ──────────────────────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    query_meta = {
        k: {"title": v["title"], "chart": v["chart"], "author": v.get("author", "Unknown")}
        for k, v in QUERIES.items()
    }
    return render_template("index.html", queries=query_meta)


@app.route("/data/<query_name>")
def data(query_name):
    if query_name not in QUERIES:
        return jsonify({"error": "Query not found"}), 404
    q = QUERIES[query_name]
    rows = run_query(q["sql"])
    return jsonify({
        "title": q["title"],
        "chart": q["chart"],
        "x": q.get("x"),
        "y": q.get("y"),
        "group": q.get("group"),
        "color": q.get("color", "#14b8a6"),
        "sql": q["sql"].strip(),
        "rows": rows
    })


if __name__ == "__main__":
    app.run(debug=True)
