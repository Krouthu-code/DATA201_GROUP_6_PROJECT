Healthcare Analytics Dashboard

A Flask + Plotly dashboard for Healthcare DB project.

Project Info
- Dataset: Kaggle Synthetic Healthcare Dataset (55,000 records)
- Database: MySQL (3NF normalized, 6 tables)
- Team: Chinmayi · Karishma · Mansi · Abhijith
- GitHub: https://github.com/Krouthu-code/DATA201_GROUP_6_PROJECT


Project Structure

```
DATA201_GROUP_6_PROJECT/
├── app.py                  ← Flask backend + all SQL queries
├── requirements.txt        ← Python dependencies
├── README.md
├── templates/
│   └── index.html          ← Frontend dashboard (must be in templates/)
└── venv/                   ← Virtual environment (created during setup)
```



Setup & Installation

1. Navigate into the project folder
```bash
cd DATA201_GROUP_6_PROJECT
```

2. Create a virtual environment
```bash
python3 -m venv venv
```

3. Activate the virtual environment
```bash
# macOS / Linux
source venv/bin/activate

```


4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Edit DB credentials in `app.py`
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "your_password",   # <-- your MySQL password
    "database": "healthcare_db"    # <-- your database name
}
```

6. Run the app
```bash
python3 app.py
```

Then open **http://localhost:5000** in your browser.

7. Deactivate when done
```bash
deactivate
```

Always run `source venv/bin/activate` before starting the app in a new terminal session.



Queries

Karishma

| Query | Chart Type | SQL Technique |
|---|---|---|
| Avg Billing by Medical Condition | Bar | GROUP BY + AVG |
| Average Patient Age by Blood Type | Bar | GROUP BY + AVG |
| Monthly Admissions Trend | Line | DATE_FORMAT + GROUP BY |
| Top 3 Conditions per Insurance Provider | Grouped Bar | `RANK() OVER (PARTITION BY ...)` |
| High-Value Patients vs Average | Bar | CTE + `CROSS JOIN` |
| Avg Billing by Condition with Running Total | Bar | Subquery + `SUM() OVER()` |
| Patients with Multiple Admissions | Bar | Subquery + `HAVING COUNT(*) > 1` |
| Rolling 3-Month Avg Admissions by Condition | Line | CTE + `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` |

Chinmayi
Queries

Mansi
Queries

Abhijith
Queries


Adding Your Queries

1. Open `app.py`
2. Find the comment block for your name and add your query:

```python
"your_query_key": {
    "author": "YourName",      # must match your name exactly
    "title": "Your Chart Title",
    "chart": "bar",            # bar | horizontal_bar | line | pie | grouped_bar
    "x": "column_for_x",
    "y": "column_for_y",
    "color": "#6366f1",
    "sql": """
        SELECT some_column, COUNT(*) AS total
        FROM   SomeTable
        GROUP  BY some_column
        ORDER  BY total DESC
    """
},
```

3. For grouped charts, also add a `"group"` key:
```python
"group": "column_to_group_by",
```

The sidebar automatically groups queries by author — no changes needed to `index.html`.
