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
   # ── CHINMAYI ──────────────────────────────────────────────

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
                SELECT
                    hospital,
                    ROUND(AVG(billing_amount), 2) AS avg_billing
                FROM   Admissions
                GROUP  BY hospital
            )
            SELECT
                a.hospital,
                COUNT(*)                      AS high_risk_count,
                ROUND(AVG(a.billing_amount), 2) AS avg_high_risk_billing,
                h.avg_billing                 AS hospital_avg_billing
            FROM   Admissions a
            JOIN   hospital_avg h ON a.hospital = h.hospital
            WHERE  a.billing_amount > h.avg_billing * 1.5
            GROUP  BY a.hospital, h.avg_billing
            ORDER  BY high_risk_count DESC
        """
    },

    "chinmayi_readmission_by_condition": {
        "author": "Chinmayi",
        "title": "Readmission Count by Condition (Subquery + HAVING)",
        "chart": "horizontal_bar",
        "x": "condition_name",
        "y": "readmission_count",
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
    # ── MANSI ─────────────────────────────────────────────────
   

"mansi_billing_by_room_number": {
    "author": "Mansi",
    "title": "Average Billing by Room Number Range",
    "chart": "bar",
    "x": "room_range",
    "y": "avg_billing",
    "color": "#10b981",
    "sql": """
        SELECT
            CASE
                WHEN room_number BETWEEN 100 AND 199 THEN '100-199'
                WHEN room_number BETWEEN 200 AND 299 THEN '200-299'
                WHEN room_number BETWEEN 300 AND 399 THEN '300-399'
                ELSE '400+'
            END AS room_range,
            COUNT(*) AS total_cases,
            ROUND(AVG(billing_amount), 2) AS avg_billing
        FROM Admissions
        GROUP BY room_range
        ORDER BY avg_billing DESC
    """
},


"mansi_gender_distribution": {
    "author": "Mansi",
    "title": "Patient Distribution by Gender",
    "chart": "pie",
    "x": "gender",
    "y": "total_patients",
    "color": "#3b82f6",
    "sql": """
        SELECT gender,
COUNT(*) AS total_patients,
ROUND(AVG(age),1) AS avg_age
FROM Patients
GROUP BY gender
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
        SELECT hospital,
               avg_billing,
               RANK() OVER (ORDER BY avg_billing DESC) AS billing_rank
        FROM (
            SELECT hospital,
                   ROUND(AVG(billing_amount), 2) AS avg_billing
            FROM Admissions
            GROUP BY hospital
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
        SELECT hospital,
               ROUND(AVG(billing_amount), 2) AS avg_billing,
               COUNT(*) AS total_admissions
        FROM Admissions
        GROUP BY hospital
        HAVING AVG(billing_amount) > (SELECT overall_billing_avg FROM overall_avg)
        ORDER BY avg_billing DESC
    """
},

"mansi_admission_type_billing_rank": {
    "author": "Mansi",
    "title": "Admission Type Billing Rank",
    "chart": "bar",
    "x": "admission_type",
    "y": "avg_billing",
    "color": "#22c55e",
    "sql": """
        SELECT admission_type,
               avg_billing,
               RANK() OVER (ORDER BY avg_billing DESC) AS billing_rank
        FROM (
            SELECT admission_type,
                   ROUND(AVG(billing_amount), 2) AS avg_billing
            FROM Admissions
            GROUP BY admission_type
        ) ranked_admission_types
        ORDER BY billing_rank
    """
},

"mansi_insurance_high_cost_subquery": {
    "author": "Mansi",
    "title": "High Cost Cases by Insurance Provider",
    "chart": "bar",
    "x": "insurance_provider",
    "y": "high_cost_cases",
    "color": "#0ea5e9",
    "sql": """
        SELECT p.insurance_provider,
               COUNT(*) AS high_cost_cases,
               ROUND(AVG(a.billing_amount), 2) AS avg_high_cost_billing
        FROM Admissions a
        JOIN Patients p ON a.patient_id = p.patient_id
        WHERE a.billing_amount > (
            SELECT AVG(billing_amount)
            FROM Admissions
        )
        GROUP BY p.insurance_provider
        ORDER BY high_cost_cases DESC
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
        SELECT hospital,
               avg_days,
               RANK() OVER (ORDER BY avg_days DESC) AS stay_rank
        FROM (
            SELECT hospital,
                   ROUND(AVG(DATEDIFF(discharge_date, date_of_admission)), 2) AS avg_days
            FROM Admissions
            GROUP BY hospital
        ) stay_summary
        ORDER BY stay_rank
    """
},
    

    # ── ABHIJITH ──────────────────────────────────────────────
    # Add your queries here following the same format:
    #
    # "your_query_key": {
    #     "author": "Abhijith",
    #     "title": "Your Chart Title",
    #     "chart": "bar",
    #     "x": "x_column",
    #     "y": "y_column",
    #     "color": "#ec4899",
    #     "sql": """
    #         SELECT ...
    #     """
    # },

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
