from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import jwt
import datetime
import os

from resume_utils import extract_text
from ai_matcher import rank_resumes

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "secret123"

UPLOAD_FOLDER = "resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

resumes = []

# ---------------- AUTO CREATE DB ----------------
def init_db():
    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        skills TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        email TEXT
    )
    """)

    # ✅ ADD THIS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        file_name TEXT,
        file_path TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- REGISTER ----------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json

    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (data["email"],))
    if cursor.fetchone():
        return jsonify({"message": "Email already exists"}), 400

    cursor.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (data["email"], generate_password_hash(data["password"]), data["role"])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Registered Successfully"})

# ---------------- LOGIN ----------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json

    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (data["email"],))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[2], data["password"]):
        token = jwt.encode(
            {
                "email": user[1],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        return jsonify({"token": token})

    return jsonify({"message": "Invalid login"}), 401

# ---------------- POST JOB ----------------
@app.route("/api/postjob", methods=["POST"])
def post_job():
    data = request.json

    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO jobs (title, description, skills) VALUES (?, ?, ?)",
        (data["title"], data["description"], data.get("skills", ""))
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Job posted successfully"})

# ---------------- GET JOBS ----------------
@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs")
    rows = cursor.fetchall()

    conn.close()

    jobs = []
    for r in rows:
        jobs.append({
            "job_id": r[0],
            "title": r[1],
            "description": r[2],
            "skills": r[3]
        })

    return jsonify(jobs)

# ---------------- APPLY JOB ----------------
@app.route("/api/apply", methods=["POST"])
def apply_job():
    data = request.json

    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO applications (job_id, email) VALUES (?, ?)",
        (data["job_id"], data["email"])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Application submitted"})

# ---------------- UPLOAD RESUME ----------------
@app.route("/api/upload", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith((".pdf", ".docx")):
        return jsonify({"error": "Only PDF or DOCX allowed"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    text = extract_text(path)

    # ✅ keep for AI
    resumes.append({
        "name": filename,
        "text": text
    })

    # ✅ NEW: save to DB
    conn = sqlite3.connect("hirex.db")
    cursor = conn.cursor()

    email = "test_user@gmail.com"  # later replace with real user

    cursor.execute(
        "INSERT INTO resumes (email, file_name, file_path) VALUES (?, ?, ?)",
        (email, filename, path)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Resume uploaded successfully"})

# ---------------- AI RANK ----------------
@app.route("/api/rank", methods=["POST"])
def rank():
    job_desc = request.json["job_description"]
    results = rank_resumes(job_desc, resumes)
    return jsonify(results)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)