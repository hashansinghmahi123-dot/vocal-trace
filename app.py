from flask import Flask, request, redirect, render_template_string
import mysql.connector

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="vocaltrace"
    )

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        number = request.form.get("number", "").strip()

        if description:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO voice_reports "
                "(caller_number, report_description) VALUES (%s, %s)",
                (number, description)
            )
            db.commit()
            cursor.close()
            db.close()
            return redirect("/")

        message = "Please enter a report description."

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM voice_reports ORDER BY report_id DESC"
    )
    reports = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>VocalTrace</title>
      <style>
        body { font-family: Arial; background: #101827; color: white;
               padding: 20px; max-width: 700px; margin: auto; }
        .card { background: #1e293b; padding: 20px;
                border-radius: 14px; margin-bottom: 18px; }
        input, textarea, button { box-sizing: border-box; width: 100%;
                padding: 12px; margin: 8px 0; border-radius: 7px; }
        button { background: #0284c7; color: white; border: 0; }
        textarea { min-height: 100px; }
        h1 { color: #38bdf8; }
      </style>
    </head>
    <body>
      <h1>VocalTrace</h1>
      <p>Voice Security Report Management</p>
      <div class="card">
        <h2>Submit a Report</h2>
        <form method="POST">
          <input name="number" placeholder="Caller number (optional)">
          <textarea name="description" required
                    placeholder="Describe the suspicious call"></textarea>
          <button type="submit">Save Report</button>
        </form>
        <p>{{ message }}</p>
      </div>
      <h2>Saved Reports</h2>
      {% for r in reports %}
      <div class="card">
        <h3>Report #{{ r.report_id }}</h3>
        <p><b>Caller:</b> {{ r.caller_number or 'Not provided' }}</p>
        <p>{{ r.report_description }}</p>
        <p><b>Risk:</b> {{ r.risk_level }}</p>
        <p><b>Status:</b> {{ r.report_status }}</p>
      </div>
      {% else %}
      <p>No reports submitted yet.</p>
      {% endfor %}
    </body>
    </html>
    """, reports=reports, message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)