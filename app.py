import os
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)


def classify_risk(description):
    text = description.lower()

    high_terms = [
        "otp", "bank password", "upi pin", "blackmail",
        "threat", "send money", "account blocked",
        "remote access"
    ]
    medium_terms = [
        "suspicious link", "unknown caller", "fake job",
        "urgent payment", "loan offer"
    ]

    if any(term in text for term in high_terms):
        return "High"
    if any(term in text for term in medium_terms):
        return "Medium"
    return "Low"


def get_db():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing.")
    return psycopg.connect(
        database_url, sslmode="require", row_factory=dict_row
    )


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


if os.environ.get("DATABASE_URL"):
    init_db()


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        number = request.form.get("number", "").strip()
        description = request.form.get("description", "").strip()

        if description:
            risk_level = classify_risk(description)
            with get_db() as db:
                db.execute("""
                    INSERT INTO voice_reports
                    (caller_number, report_description, risk_level)
                    VALUES (%s, %s, %s)
                """, (number, description, risk_level))
            return redirect("/")

        message = "Please enter a report description."

    with get_db() as db:
        reports = db.execute("""
            SELECT report_id, caller_number, report_description,
                   risk_level, report_status, created_at
            FROM voice_reports
            ORDER BY report_id DESC
        """).fetchall()

    total = len(reports)
    high = sum(r["risk_level"] == "High" for r in reports)
    medium = sum(r["risk_level"] == "Medium" for r in reports)
    low = sum(r["risk_level"] == "Low" for r in reports)

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VocalTrace | Cyber Security</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0; padding: 22px; color: #d1ffe3;
    background: #050a0e;
    background-image: radial-gradient(circle at top right,#073b2b,transparent 38%);
    font-family: "Courier New", monospace;
}
main { max-width: 1100px; margin: auto; }
h1 { color: #39ff88; text-shadow: 0 0 12px #39ff8844; letter-spacing: 3px; }
h2 { color: #39ff88; }
.subtitle { color: #8ca99a; }
.status { color: #39ff88; font-size: 13px; }
.stats {
    display: grid; grid-template-columns: repeat(4,minmax(0,1fr));
    gap: 12px; margin: 22px 0;
}
.card {
    background: #0b1518; border: 1px solid #17613f;
    padding: 18px; border-radius: 10px; margin-bottom: 16px;
    overflow-wrap: anywhere; box-shadow: 0 0 12px #00ff8810;
}
.stat-number { font-size: 30px; font-weight: bold; color: #39ff88; }
.high { color: #ff6473; }
.medium { color: #ffbf69; }
.low { color: #39ff88; }
label { display: block; margin-top: 12px; }
input, textarea, button {
    width: 100%; padding: 12px; margin-top: 7px;
    border-radius: 5px; font: inherit;
}
input, textarea {
    color: #d1ffe3; background: #050b0e; border: 1px solid #236b49;
}
textarea { min-height: 100px; resize: vertical; }
button {
    background: #39ff88; color: #041009; border: 0;
    cursor: pointer; font-weight: bold; margin-top: 14px;
}
.report { border-left: 3px solid #17613f; }
.badge { font-weight: bold; }
.notice { color: #ff6473; }
.small { color: #8ca99a; font-size: 13px; }
footer { text-align: center; color: #628574; padding: 18px; font-size: 12px; }
@media(max-width:650px) {
    body { padding: 12px; }
    .stats { grid-template-columns: repeat(2,minmax(0,1fr)); }
    .stat-number { font-size: 25px; }
}
</style>
</head>
<body>
<main>
    <h1>VocalTrace<span class="status"> ● SYSTEM ONLINE</span></h1>
    <p class="subtitle">VOICE SECURITY // THREAT REPORT CONSOLE</p>

    <section class="stats">
        <div class="card">
            <div class="small">TOTAL REPORTS</div>
            <div class="stat-number">{{ total }}</div>
        </div>
        <div class="card">
            <div class="small">HIGH RISK</div>
            <div class="stat-number high">{{ high }}</div>
        </div>
        <div class="card">
            <div class="small">MEDIUM RISK</div>
            <div class="stat-number medium">{{ medium }}</div>
        </div>
        <div class="card">
            <div class="small">LOW RISK</div>
            <div class="stat-number low">{{ low }}</div>
        </div>
    </section>

    <section class="card">
        <h2>&gt; Submit New Report</h2>
        <form method="POST">
            <label for="number">Caller number (optional)</label>
            <input id="number" name="number" maxlength="30"
                   placeholder="Enter caller number">
            <label for="description">Report description</label>
            <textarea id="description" name="description" required
                      placeholder="Describe the suspicious call..."></textarea>
            <button type="submit">+ Save &amp; Analyze Report</button>
        </form>
        <p class="notice">{{ message }}</p>
    </section>

    <h2>&gt; Recent Reports ({{ total }})</h2>
    {% for report in reports %}
    <section class="card report">
        <h3>REPORT #{{ report.report_id }}</h3>
        <p><span class="small">CALLER:</span>
           {{ report.caller_number or 'Not provided' }}</p>
        <p><span class="small">DESCRIPTION:</span><br>
           {{ report.report_description }}</p>
        <p><span class="small">RISK:</span>
           <span class="badge
           {% if report.risk_level == 'High' %}high
           {% elif report.risk_level == 'Medium' %}medium
           {% else %}low{% endif %}">
           {{ report.risk_level|upper }}</span></p>
        <p><span class="small">STATUS:</span> {{ report.report_status }}</p>
        <p class="small">CREATED: {{ report.created_at }}</p>
    </section>
    {% else %}
    <section class="card">No reports yet. Submit your first report above.</section>
    {% endfor %}

    <footer>VocalTrace // Cybersecurity &amp; Database Project</footer>
</main>
</body>
</html>
""", reports=reports, message=message,
        total=total, high=high, medium=medium, low=low)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
