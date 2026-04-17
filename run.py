from flask import Flask, redirect, render_template, request, session, url_for,flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection, create_tables
from functools import wraps
from datetime import datetime
import numpy as np
import cv2
from register import register_student
from recognizer import start_face_attendance, recognize, load_embeddings, mark_attendance_db, stop_camera
import threading
import os
import smtplib
import random
import time
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

app = Flask(__name__)
app.secret_key = "supersecret"

otp_storage = {}
GMAIL = ""
APP_PASSWORD = ""


COLLEGE_LAT = 18.998951751419046
COLLEGE_LON = 72.81767908174002



MAX_DISTANCE_KM = 0.1    # 100 meters radius

@app.context_processor
def inject_user():
    return dict(
        user_name=session.get("user_name"),
        user_prn=session.get("user_prn")
    )

create_tables()



def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper

def for_staff_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "staff":
            return redirect("/dashboard")
        return f(*args, **kwargs)
    return wrapper

def for_student_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "student":
            return redirect("/dashboard_staff")
        return f(*args, **kwargs)
    return wrapper

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def send_otp(email):
    otp = str(random.randint(100000, 999999))

    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    subject = "Your OTP - AI Attendance"
    body = f"Your OTP for registration is: {otp}\n\nValid for 5 minutes only."
    message = f"Subject: {subject}\n\n{body}"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(GMAIL, APP_PASSWORD)
    server.sendmail(GMAIL, email, message)
    server.quit()

    print(f"OTP sent to {email}: {otp}")

@app.route("/send_otp", methods=["POST"])
def send():
    email = request.form.get("email")

    if not email:
        return {"status": "error", "message": "Email required"}

    send_otp(email)
    return {"status": "success", "message": "OTP sent to " + email}



@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email")
    otp = request.form.get("otp")

    record = otp_storage.get(email)

    if not record:
        return {"status": "error", "message": "OTP not sent yet"}

    
    if time.time() - record["time"] > 300:
        otp_storage.pop(email)
        return {"status": "error", "message": "OTP expired. Request a new one"}

    if record["otp"] != otp:
        return {"status": "error", "message": "Invalid OTP"}

    session["otp_verified_email"] = email
    otp_storage.pop(email)

    return {"status": "success", "message": "Email verified"}





@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND role=?",
            (email, role)
        )

        user = cur.fetchone()

        if not user:
            flash("User does not exist", "error")
            return redirect("/")

        if not check_password_hash(user["password"], password):
            flash("Incorrect password", "error")
            return redirect("/")


        if user["role"] == "student":

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_department"] = user["department"]
            session["role"] = "student"

            cur.execute(
                """SELECT students.prn 
                   FROM users 
                   JOIN students ON users.id = students.user_id
                   WHERE users.id = ?""",
                (session["user_id"],)
            )

            student = cur.fetchone()
            session["user_prn"] = student["prn"]

            conn.close()
            return redirect("/dashboard")


        elif user["role"] == "staff":

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_department"] = user["department"]
            session["role"] = "staff"

            conn.close()
            return redirect("/dashboard_staff")

    return render_template("home.html")





@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        prn = request.form.get("prn")
        department = request.form.get("department").upper()
        email = request.form.get("email")
        password = request.form.get("password")

        if session.get("otp_verified_email") != email:
            flash("Please verify your email via OTP first", "error")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """INSERT INTO users (name, department, email, password, role)
               VALUES (?, ?, ?, ?, ?)""",
            (name, department, email, hashed_password, "student")
        )

        user_id = cur.lastrowid

        cur.execute(
            "INSERT INTO students (user_id, prn) VALUES (?, ?)",
            (user_id, prn)
        )

        conn.commit()
        conn.close()

        session.pop("otp_verified_email")
        return redirect(url_for("home"))

    return render_template("register.html")



@app.route("/dashboard")
@login_required
@for_student_only
def dashboard():
    print(session.get("user_department"))

    department = session.get("user_department")
    id = session.get("user_id")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*) AS total FROM lectures
    WHERE department = ? 
    """,(department,))

    row = cur.fetchone()
    total_lec = row["total"] if row else 0

    cur.execute("""
    SELECT COUNT(lecture_id) AS total FROM attendance
    WHERE user_id = ?
    AND status = "Present"
    """,(id,))

    row = cur.fetchone()
    attended_lec = row["total"] if row else 0

    cur.execute("""
    SELECT COUNT(lecture_id) AS total FROM attendance
    WHERE user_id = ?
    AND status = "Absent"
    """,(id,))

    row = cur.fetchone()
    missed_lec = row["total"] if row else 0

    if total_lec == 0:
        percentage = 0
    else:
        percentage = round((attended_lec / total_lec) * 100, 2)

    conn.close()

    return render_template("dashboard.html", total_lec= total_lec, attended_lec=attended_lec,missed=missed_lec,percentage=percentage)


@app.route("/dashboard_staff")
@login_required
@for_staff_only
def dashboard_staff():
    department = session.get("user_department")
    staff_name = session.get("user_name")

    conn = get_connection()
    cur = conn.cursor()

    # ── Total students in department
    cur.execute("""
        SELECT COUNT(*) as total FROM users
        WHERE department = ? AND role = 'student'
    """, (department,))
    total_students = cur.fetchone()["total"]

    # ── Today's attendance
    cur.execute("""
        SELECT COUNT(DISTINCT attendance.user_id) as present
        FROM attendance
        JOIN lectures ON attendance.lecture_id = lectures.lecture_id
        WHERE lectures.department = ?
        AND attendance.date = date('now','localtime')
    """, (department,))
    today_present = cur.fetchone()["present"]

    # ── Weekly attendance (Mon to Fri)
    weekly = []
    today = datetime.today()
    # go back to Monday of current week
    monday = today - timedelta(days=today.weekday())

    for i in range(5):  # Mon to Fri
        day = monday + timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        day_label = day.strftime("%a")  # Mon, Tue etc

        cur.execute("""
            SELECT COUNT(DISTINCT attendance.user_id) as present
            FROM attendance
            JOIN lectures ON attendance.lecture_id = lectures.lecture_id
            WHERE lectures.department = ?
            AND attendance.date = ?
        """, (department, date_str))
        present = cur.fetchone()["present"]

        absent = total_students - present
        weekly.append({
            "day": day_label,
            "present": present,
            "absent": absent if absent > 0 else 0
        })

    # ── Recent activity — last 5 attendance records
    cur.execute("""
        SELECT users.name, students.prn,
               attendance.time, attendance.status, attendance.date
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        JOIN students ON users.id = students.user_id
        JOIN lectures ON attendance.lecture_id = lectures.lecture_id
        WHERE lectures.department = ?
        ORDER BY attendance.id DESC
        LIMIT 5
    """, (department,))
    recent = cur.fetchall()

    # ── Active lecture check
    cur.execute("""
        SELECT * FROM lectures
        WHERE department = ? AND is_active = 1
    """, (department,))
    active_lecture = cur.fetchone()

    conn.close()

    # today's attendance rate
    rate = round((today_present / total_students * 100)) if total_students > 0 else 0

    return render_template("dashboard_staff.html",
        staff_name=staff_name,
        total_students=total_students,
        today_present=today_present,
        today_rate=rate,
        weekly=weekly,
        recent=recent,
        active_lecture=active_lecture
    )

@app.route("/view")
@login_required
@for_student_only
def view():

    department = session.get("user_department")
    id = session.get("user_id")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT lectures.subject, lectures.start_time, attendance.status, attendance.date
    FROM lectures
    LEFT JOIN attendance ON lectures.lecture_id = attendance.lecture_id
    AND attendance.user_id = ?
    WHERE lectures.department = ?
    AND lectures.is_active = 0
    ORDER BY lectures.start_time DESC
    LIMIT 10
    """,(id,department))

    past_attendance = cur.fetchall()

    cur.execute("""
    SELECT COUNT(*) AS total FROM lectures
    WHERE department = ? 
    """,(department,))

    row = cur.fetchone()
    total_lec = row["total"] if row else 0

    cur.execute("""
    SELECT COUNT(lecture_id) AS total FROM attendance
    WHERE user_id = ?
    AND status = "Present"
    """,(id,))

    row = cur.fetchone()
    attended_lec = row["total"] if row else 0

    cur.execute("""
    SELECT COUNT(lecture_id) AS total FROM attendance
    WHERE user_id = ?
    AND status = "Absent"
    """,(id,))

    row = cur.fetchone()
    missed_lec = row["total"] if row else 0

    if total_lec == 0:
        percentage = 0
    else:
        percentage = round((attended_lec / total_lec) * 100, 2)


    conn.close()

    return render_template("view.html", total_lec= total_lec, attended_lec=attended_lec, missed=missed_lec, percentage=percentage, past_attendance=past_attendance)



@app.route("/register_img", methods=["GET"])
@login_required
@for_student_only
def register_img_page():
    return render_template("register_img.html")


@app.route("/register_img", methods=["POST"])
@login_required
@for_student_only
def register_img():

    user_id = session["user_id"]
    name = session["user_name"]
    prn = session["user_prn"]

    file = request.files.get("image")

    if not file:
        return {"status": "error", "message": "No image uploaded"}


    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    result = register_student(user_id, name, prn, image)

    print("REGISTER API CALLED")
    print(request.files)

    return {"status": "success", "message": result}


@app.route("/mark")
@login_required
@for_student_only
def mark():
    return render_template("mark.html")



@app.route("/face_mark", methods=["POST"])
@login_required
@for_student_only
def face_mark():

    file = request.files.get("image")
    lat = request.form.get("lat")
    lon = request.form.get("lon")


    if not lat or not lon:
        return {"status": "error", "message": "Location access required"}

    distance = get_distance(
        float(lat), float(lon),
        COLLEGE_LAT, COLLEGE_LON
    )

    print(f"Student distance from college: {distance:.3f} km")

    if distance > MAX_DISTANCE_KM:
        return {
            "status": "error",
            "message": f"You are too far from college ({round(distance*1000)}m away)"
        }
    
    if not file:
        return {"status":"error","message":"No image"}

    file_bytes = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    print("📸 Frame received")

    department = session.get("user_department")

    

    embeddings, names, reg_nos = load_embeddings()

    print("Embeddings loaded:", len(embeddings))

    results = recognize(frame, embeddings, names, reg_nos)

    print("Faces detected:", len(results))

    for (_, _, _, _, name, prn, _) in results:
        print("Detected:", name, prn)

        if prn:
            mark_attendance_db(prn, department)
            return {"status":"success","message":"Attendance marked via face"}

    return {"status":"error","message":"Face not recognized"}


@app.route("/mark_attendance", methods=["POST"])
@login_required
@for_student_only
def mark_attendance():

    user_id = session["user_id"]
    department = session["user_department"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT lecture_id, subject, staff_name
    FROM lectures
    WHERE department=? AND is_active=1
    ORDER BY lecture_id DESC
    LIMIT 1
    """,(department,))

    lecture = cur.fetchone()

    if not lecture:
        conn.close()
        return {"status":"error","message":"No lecture running"}

    lecture_id = lecture["lecture_id"]
    subject = lecture["subject"]
    staff = lecture["staff_name"]

   
    cur.execute("""
    SELECT * FROM attendance
    WHERE user_id=? AND lecture_id=?
    """,(user_id, lecture_id))

    existing = cur.fetchone()

    if existing:
        conn.close()
        return {"status":"error","message":"Attendance already marked"}

    cur.execute("""
    INSERT INTO attendance(user_id,lecture_id,subject,staff_name, department,date,time,status)
    VALUES(?,?,?,?,?,date('now'),time('now','localtime'),'Present')
    """,(user_id,lecture_id,subject,staff, department))

    conn.commit()
    conn.close()

    return {"status":"success","message":"Attendance marked"}





@app.route("/start_lec", methods=["GET"])
@login_required
@for_staff_only
def start_lec_page():

    department = session.get("user_department")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM lectures
        WHERE department = ?
        AND is_active = 1
    """,(department,))
    

    lecture = cur.fetchone()

    
    cur.execute("""
        SELECT * FROM subjects
        WHERE department = ?
    """,(department,))

    subs = cur.fetchall()


    students = []
    if lecture:
        cur.execute("""
            SELECT DISTINCT users.name, students.prn, attendance.time, attendance.status
            FROM attendance
            JOIN users ON attendance.user_id = users.id
            JOIN students ON users.id = students.user_id
            WHERE attendance.lecture_id = ?
            ORDER BY attendance.time ASC
        """, (lecture["lecture_id"],))

        students = cur.fetchall()

    conn.close()
    return render_template("start_lec.html", lecture=lecture, students=students, subs = subs)






@app.route("/start_lec", methods=["POST"])
@login_required
@for_staff_only
def start_lec():

    subject = request.form.get("subject")
    staff_name = session.get("user_name")
    department = session.get("user_department")
    
    
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    if not department:
        flash("Department not found in session", "error")
        return redirect(url_for("home"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM lectures
        WHERE department = ?
        AND is_active = 1
    """, (department,))

    existing = cur.fetchone()

    if existing:
        conn.close()
        flash("A lecture is already running for your department", "error")
        return redirect("/start_lec")

    cur.execute("""
        INSERT INTO lectures
        (subject, department, staff_name, start_time, end_time, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (subject, department, staff_name,start_time, end_time))


    cur.execute("""
        SELECT * FROM lectures
        WHERE department = ?
        AND is_active = 1
        ORDER BY lecture_id DESC
        LIMIT 1
    """, (department,))

    lecture1 = cur.fetchone()

    print(lecture1)
    print(department)

    conn.commit()
    conn.close()

    return redirect("/start_lec")




@app.route("/stop_lec", methods=["POST"])
@login_required
@for_staff_only
def stop_lec():

    print("STOP BUTTON CLICKED")   # DEBUG
    department = session.get("user_department")
    print(department)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM lectures
        WHERE department = ?
        AND is_active = 1
    """, (department,))

    lecture = cur.fetchone()

    if not lecture:
        conn.close()
        flash("No active lecture found", "error")
        return redirect("/start_lec")
    
    lecture_id = lecture["lecture_id"]
    subject = lecture["subject"]
    staff = lecture["staff_name"]
    department = lecture["department"]

    print(lecture, subject, staff)
    
    cur.execute("""
        UPDATE lectures
        SET is_active = 0,
        end_time = datetime('now')
        WHERE lecture_id = ?
    """, (lecture_id,))

    # cur.execute("""
    #     SELECT users.name, students.prn, attendance.subject, attendance.lecture_id,
    #            attendance.date, attendance.time, attendance.status
    #     FROM attendance
    #     JOIN users ON attendance.user_id = users.id
    #     JOIN students ON users.id = students.user_id
    #     ORDER BY attendance.date DESC
    # """)

    # records = cur.fetchall()

    # print("\n--- Attendance Records ---")

    # for r in records:
    #     print(
    #         r["name"],"|",r["prn"],"|",r["subject"],"|",r["lecture_id"],"|",r["date"],"|",r["time"],"|",r["status"]
    #     )

    # print("--------------------------\n")

    cur.execute("""
        SELECT id FROM users
        WHERE role = 'student' AND department = ?
    """, (department,))
    students = cur.fetchall()

    cur.execute("""
    SELECT user_id FROM attendance 
    WHERE lecture_id = ? AND status = 'Present'
    """, (lecture_id,))

    present_students = {row["user_id"] for row in cur.fetchall()}

    for student in students:
        if student["id"] not in present_students:
            cur.execute("""
            INSERT OR IGNORE INTO attendance (user_id, lecture_id,subject,staff_name,department,date,time, status)
            VALUES (?, ?,?,?,?,date('now'),time('now','localtime'), "Absent")
            """, (student["id"], lecture_id, subject, staff, department))


    conn.commit()
    conn.close()

    flash("Lecture stopped successfully", "success")
    return redirect("/start_lec")





@app.route("/overview")
@login_required
@for_staff_only
def overview():
    return render_template("overview.html")



@app.route("/check_lecture")
@login_required
def check_lecture():

    department = session.get("user_department")

    if not department:
        return {"active": False}

    conn = get_connection()
    cur = conn.cursor()


    cur.execute("""
        SELECT subject, staff_name
        FROM lectures
        WHERE department = ?
        AND is_active = 1
    """, (department,))

    lecture = cur.fetchone()

    conn.close()

    if lecture:
        return {
            "active": True,
            "subject": lecture["subject"],
            "teacher": lecture["staff_name"],
        }

    return {"active": False}

@app.route("/weekly_attendance")
@login_required
def weekly_attendance():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT date,
               COUNT(CASE WHEN status='Present' THEN 1 END) * 100.0 / COUNT(*) as percentage
        FROM attendance
        WHERE user_id = ?
        GROUP BY date
        ORDER BY date
    """, (session["user_id"],))

    data = cur.fetchall()

    return {
        "labels": [row[0] for row in data],
        "values": [round(row[1], 2) for row in data]
    }

@app.route("/subject_attendance")
@login_required
def subject_attendance():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT subject,
               COUNT(CASE WHEN status='Present' THEN 1 END) as present,
               COUNT(*) as total
        FROM attendance
        WHERE user_id = ?
        GROUP BY subject
    """, (session["user_id"],))

    data = cur.fetchall()

    return {
        "subjects": [
            {
                "subject": row[0],
                "present": row[1],
                "total": row[2],
                "percentage": round((row[1] / row[2]) * 100, 2) if row[2] else 0
            }
            for row in data
        ]
    }

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")