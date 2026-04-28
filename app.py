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
    # Add your queries here following the same format:
    #
    # "your_query_key": {
    #     "author": "Chinmayi",
    #     "title": "Your Chart Title",
    #     "chart": "bar",        # bar | horizontal_bar | line | pie | grouped_bar
    #     "x": "x_column",
    #     "y": "y_column",
    #     "color": "#6366f1",
    #     "sql": """
    #         SELECT ...
    #     """
    # },

    # ── MANSI ─────────────────────────────────────────────────
    # Add your queries here following the same format:
    #
    # "your_query_key": {
    #     "author": "Mansi",
    #     "title": "Your Chart Title",
    #     "chart": "bar",
    #     "x": "x_column",
    #     "y": "y_column",
    #     "color": "#f59e0b",
    #     "sql": """
    #         SELECT ...
    #     """
    # },

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
