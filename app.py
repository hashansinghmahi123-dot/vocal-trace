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
        font-family: "Courier New", monospace;
        background: #050a0e;
        color: #d1ffe3;
        padding: 20px;
        max-width: 1100px;
        margin: auto;
        background-image:
            radial-gradient(circle at top right, #073b2b 0, transparent 35%);
    }

    h1 {
        color: #39ff88;
        text-shadow: 0 0 12px #00ff8844;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }

    h2 {
        color: #39ff88;
        border-bottom: 1px solid #145c3b;
        padding-bottom: 10px;
    }

    .subtitle {
        color: #8ca99a;
        margin-bottom: 25px;
    }

    .card {
        background: #0b1518;
        border: 1px solid #17613f;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 18px;
        overflow-wrap: anywhere;
        box-shadow: 0 0 12px #00ff8810;
    }

    input, textarea, button {
        width: 100%;
        padding: 13px;
        margin: 8px 0;
        border-radius: 6px;
        font-size: 16px;
        font-family: inherit;
    }

    input, textarea {
        background: #050b0e;
        color: #d1ffe3;
        border: 1px solid #236b49;
    }

    input:focus, textarea:focus {
        outline: 1px solid #39ff88;
        box-shadow: 0 0 10px #39ff8833;
    }

    textarea {
        min-height: 110px;
        resize: vertical;
    }

    button {
        background: #39ff88;
        color: #041009;
        border: none;
        cursor: pointer;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    button:hover {
        background: #a0ffc5;
        box-shadow: 0 0 14px #39ff8877;
    }

    .label {
        color: #39ff88;
        font-weight: bold;
    }

    .notice {
        color: #ff5d6c;
    }

    .empty {
        color: #8ca99a;
    }

    footer {
        color: #628574;
        text-align: center;
        margin-top: 25px;
        font-size: 13px;
    }

    @media (max-width: 600px) {
        body {
            padding: 12px;
        }

        .card {
            padding: 15px;
        }

        h1 {
            font-size: 25px;
        }
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
