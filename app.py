import os
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
def classify_risk(description):
    text = description.lower()

    high_terms = [
        "otp", "bank password", "upi pin",
        "blackmail", "threat", "send money",
        "account blocked", "remote access"
    ]

    medium_terms = [
        "suspicious link", "unknown caller",
        "fake job", "urgent payment", "loan offer"
    ]

    if any(term in text for term in high_terms):
        return "High"
    elif any(term in text for term in medium_terms):
        return "Medium"
    else:
        return "Low"


# Connect to the PostgreSQL database
def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Set it in your environment."
        )

    return psycopg.connect(
        database_url,
        sslmode="require",
        row_factory=dict_row
    )


# Create the reports table automatically
def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS voice_reports (
                report_id SERIAL PRIMARY KEY,
                caller_number VARCHAR(30),
                report_description TEXT NOT NULL,
                risk_level VARCHAR(20) DEFAULT 'Unreviewed',
                report_status VARCHAR(30) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Initialize the database when DATABASE_URL is configured
if os.environ.get("DATABASE_URL"):
    init_db()


# Main page
@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        number = request.form.get("number", "").strip()
        description = request.form.get("description", "").strip()
        risk_level = classify_risk(description)

        if description:
            with get_db() as db:
                db.execute(
    """
    INSERT INTO voice_reports
    (caller_number, report_description, risk_level)
    VALUES (%s, %s, %s)
    """,
    (number, description, risk_level)
)
            return redirect("/")

        message = "Please enter a report description."

    with get_db() as db:
        reports = db.execute("""
            SELECT report_id, caller_number, report_description,
                   risk_level, report_status, created_at
            FROM voice_reports
            ORDER BY report_id DESC
        """).fetchall()

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>VocalTrace</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                padding: 20px;
                max-width: 750px;
                margin: auto;
            }

            h1 {
                color: #38bdf8;
                margin-bottom: 5px;
            }

            .subtitle {
                color: #cbd5e1;
                margin-bottom: 25px;
            }

            .card {
                background: #1e293b;
                padding: 20px;
                border-radius: 14px;
                margin-bottom: 18px;
                overflow-wrap: anywhere;
            }

            input, textarea, button {
                width: 100%;
                padding: 12px;
                margin: 8px 0;
                border-radius: 8px;
                font-size: 16px;
            }

            input, textarea {
                background: #f8fafc;
                color: #0f172a;
                border: 1px solid #cbd5e1;
            }

            textarea {
                min-height: 110px;
                resize: vertical;
            }

            button {
                background: #0284c7;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: bold;
            }

            button:hover {
                background: #0369a1;
            }

            .label {
                color: #7dd3fc;
                font-weight: bold;
            }

            .notice {
                color: #fca5a5;
            }

            .empty {
                color: #cbd5e1;
            }

            footer {
                color: #94a3b8;
                text-align: center;
                margin-top: 25px;
                font-size: 13px;
            }
        </style>
    </head>

    <body>
        <h1>VocalTrace</h1>
        <p class="subtitle">
            Voice Security Report Management System
        </p>

        <div class="card">
            <h2>Submit a Report</h2>

            <form method="POST">
                <label for="number">Caller Number (optional)</label>
                <input
                    id="number"
                    type="text"
                    name="number"
                    maxlength="30"
                    placeholder="Enter caller number"
                >

                <label for="description">Report Description</label>
                <textarea
                    id="description"
                    name="description"
                    required
                    placeholder="Describe the suspicious call..."
                ></textarea>

                <button type="submit">Save Report</button>
            </form>

            <p class="notice">{{ message }}</p>
        </div>

        <h2>Saved Reports ({{ reports|length }})</h2>

        {% for report in reports %}
        <div class="card">
            <h3>Report #{{ report.report_id }}</h3>

            <p>
                <span class="label">Caller:</span>
                {{ report.caller_number or 'Not provided' }}
            </p>

            <p>
                <span class="label">Description:</span><br>
                {{ report.report_description }}
            </p>

            <p>
                <span class="label">Risk:</span>
                {{ report.risk_level }}
            </p>

            <p>
                <span class="label">Status:</span>
                {{ report.report_status }}
            </p>

            <p>
                <span class="label">Created:</span>
                {{ report.created_at }}
            </p>
        </div>
        {% else %}
        <p class="empty">No reports submitted yet.</p>
        {% endfor %}

        <footer>
            VocalTrace | Cybersecurity & Database Project
        </footer>
    </body>
    </html>
    """, reports=reports, message=message)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
