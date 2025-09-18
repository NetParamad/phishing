---

## 🛠️ Dependencies
- Python 3.10+
- Flask
- Flask-SQLAlchemy

# สร้างและ activate venv
python -m venv .venv

# ติดตั้ง package
pip install flask flask_sqlalchemy

export FLASK_APP=app.py
export FLASK_ENV=development   # optional สำหรับ debug

# ติดตั้ง DB
flask initdb

# วิธี Run
flask run
# หรือ
python app.py