import sqlite3
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random
import numpy as np

DB_NAME = "database.db"
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# ── 3 STAFF ──────────────────────────────────────────
# staff = [
#     ("Prof. Sharma", "AI", "sharma@college.com"),
#     ("Prof. Mehta",  "AI", "mehta@college.com"),
#     ("Prof. Verma",  "AI", "verma@college.com"),
# ]

# department = "AI"

# staff_ids = []
# for name, dept, email in staff:
#     cur.execute("""
#         INSERT OR IGNORE INTO users (name, department, email, password, role)
#         VALUES (?, ?, ?, ?, 'staff')
#     """, (name, dept, email, generate_password_hash("staff123")))
#     cur.execute("SELECT id FROM users WHERE email=?", (email,))
#     staff_ids.append(cur.fetchone()[0])

# # ── 10 STUDENTS ───────────────────────────────────────
# students = [
#     ("Aarya",   "AI", "aarya@college.com",   "23UF12345AI000"),
#     ("Raj",     "AI", "raj@college.com",     "23UF12345AI001"),
#     ("Priya",   "AI", "priya@college.com",   "23UF12345AI002"),
#     ("Rohan",   "AI", "rohan@college.com",   "23UF12345AI003"),
#     ("Sneha",   "AI", "sneha@college.com",   "23UF12345AI004"),
#     ("Amit",    "AI", "amit@college.com",    "23UF12345AI005"),
#     ("Kavya",   "AI", "kavya@college.com",   "23UF12345AI006"),
#     ("Vishal",  "AI", "vishal@college.com",  "23UF12345AI007"),
#     ("Pooja",   "AI", "pooja@college.com",   "23UF12345AI008"),
#     ("Nikhil",  "AI", "nikhil@college.com",  "23UF12345AI009"),
# ]

# student_user_ids = []
# for name, dept, email, prn in students:
#     cur.execute("""
#         INSERT OR IGNORE INTO users (name, department, email, password, role)
#         VALUES (?, ?, ?, ?, 'student')
#     """, (name, dept, email, generate_password_hash("student123")))
#     cur.execute("SELECT id FROM users WHERE email=?", (email,))
#     user_id = cur.fetchone()[0]
#     cur.execute("INSERT OR IGNORE INTO students (user_id, prn) VALUES (?, ?)", (user_id, prn))
#     student_user_ids.append(user_id)

# # ── 30 LECTURES ───────────────────────────────────────
# subjects = [
#     "Machine Learning",
#     "Deep Learning",
#     "Data Mining",
#     "Big Data Analytics",
#     "Natural Language Processing"
# ]

# staff_names = ["Prof. Sharma", "Prof. Mehta", "Prof. Verma"]

# # spread across last 3 weeks
# base_date = date.today() - timedelta(days=21)

# lecture_ids = []
# for i in range(30):
#     subject    = subjects[i % len(subjects)]
#     staff_name = staff_names[i % len(staff_names)]
#     lec_date   = base_date + timedelta(days=i % 21)  # spread over 21 days
#     start_time = f"{lec_date} 09:00:00"
#     end_time   = f"{lec_date} 10:00:00"

#     cur.execute("""
#         INSERT INTO lectures (subject, staff_name, department, start_time, end_time, is_active)
#         VALUES (?, ?, 'AI', ?, ?, 0)
#     """, (subject, staff_name, start_time, end_time))

#     lecture_ids.append(cur.lastrowid)

# # ── ATTENDANCE ────────────────────────────────────────
# # each student attends ~80% of lectures randomly
# for lecture_id in lecture_ids:

#     # get subject and staff for this lecture
#     cur.execute("SELECT subject, staff_name, start_time FROM lectures WHERE lecture_id=?", (lecture_id,))
#     lec = cur.fetchone()
#     lec_date = lec[2][:10]   # extract date part

#     for user_id in student_user_ids:

#         # 80% chance of attending
#         if random.random() < 0.80:
#             status = "Present"
#             time = "09:15:00"
#         else:
#             status = "Absent"
#             time = "00:00:00"   # or keep None / same time

#         cur.execute("""
#             INSERT OR IGNORE INTO attendance
#             (user_id, lecture_id, subject, staff_name, department, date, time, status)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (user_id, lecture_id, lec[0], lec[1], department, lec_date, time, status))

# conn.commit()
# conn.close()
# print("✅ Done — 3 staff, 10 students, 30 lectures, attendance inserted")

