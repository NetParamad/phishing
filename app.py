from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///phish_train.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Models
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False)
    name = db.Column(db.String(128))
    department = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_email = db.Column(db.String(256), nullable=True)
    event_type = db.Column(db.String(64))  # "view_training", "clicked_sim", "reported"
    meta = db.Column("metadata", db.String(512))   # attribute name 'meta' to avoid conflict
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/training")
def training():
    return render_template("training.html")

@app.route("/training/complete", methods=["POST"])
def training_complete():
    email = request.form.get("email")
    log = EventLog(participant_email=email, event_type="view_training", meta="completed_quiz")
    db.session.add(log)
    db.session.commit()
    flash("ขอบคุณที่ทำแบบทดสอบ! ผลได้ถูกบันทึกแล้ว", "success")
    return redirect(url_for("index"))

@app.route("/report", methods=["GET","POST"])
def report():
    if request.method == "POST":
        email = request.form.get("email") or "anonymous"
        details = request.form.get("details") or ""
        log = EventLog(participant_email=email, event_type="reported", meta=details)
        db.session.add(log)
        db.session.commit()
        flash("เราได้รับการรายงานของคุณแล้ว — ขอบคุณที่ช่วยเสริมความปลอดภัย", "success")
        return redirect(url_for("index"))
    return render_template("report.html")

@app.route("/admin")
def admin():
    total = Participant.query.count()
    clicks = EventLog.query.filter_by(event_type="clicked_sim").count()
    reports = EventLog.query.filter_by(event_type="reported").count()
    training_completed = EventLog.query.filter_by(event_type="view_training").count()
    events = EventLog.query.order_by(EventLog.created_at.desc()).limit(200).all()
    return render_template("admin.html", total=total, clicks=clicks, reports=reports,
                           training_completed=training_completed, events=events)

@app.route("/admin/export")
def admin_export():
    events = EventLog.query.order_by(EventLog.created_at.asc()).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["id","participant_email","event_type","metadata","created_at"])
    for e in events:
        cw.writerow([e.id, e.participant_email, e.event_type, e.meta, e.created_at.isoformat()])
    mem = io.BytesIO()
    mem.write(si.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, download_name="phish_training_events.csv", as_attachment=True)

@app.route("/simulated-link/<token>")
def simulated_link(token):
    participant = request.args.get("email")
    log = EventLog(participant_email=participant, event_type="clicked_sim", meta=f"token={token}")
    db.session.add(log)
    db.session.commit()
    return render_template("simulated_result.html", token=token, participant=participant)

@app.route("/admin/add_participant", methods=["POST"])
def add_participant():
    email = request.form.get("email")
    name = request.form.get("name")
    dept = request.form.get("department")
    if email:
        p = Participant(email=email, name=name, department=dept)
        try:
            db.session.add(p)
            db.session.commit()
            flash("เพิ่มผู้เข้าร่วมเรียบร้อย", "success")
        except Exception as e:
            db.session.rollback()
            flash("ไม่สามารถเพิ่มผู้เข้าร่วม (อาจมีอยู่แล้ว)", "danger")
    return redirect(url_for("admin"))

@app.cli.command("initdb")
def initdb():
    db.create_all()
    print("DB initialized.")

if __name__ == "__main__":
    app.run(debug=True)
