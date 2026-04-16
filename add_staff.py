from database import get_connection, create_tables
import csv
from werkzeug.security import generate_password_hash

conn = get_connection()
cur = conn.cursor()

create_tables()

with open("staff.csv", newline='') as file:
    reader = csv.DictReader(file)

    for row in reader:
        name = row["name"]
        department = row["department"].upper()
        email = row["email"]
        password = generate_password_hash(f"collegename{department}")
        role = "staff"

    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (name, department, email, password, role) VALUES (?, ?, ?, ?, ?)",
            (name, department, email, password, "staff")
        )
        print(f"{email} added")
    else:
        print(f"{email} already exists")



with open("subs.csv", newline='') as file:
    reader = csv.DictReader(file)

    for row in reader:
        sub = row["Subjects"]
        department = row["Department"].upper()

        cur.execute("SELECT * FROM subjects WHERE subject=? AND department=?", (sub, department))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO subjects (subject, department) VALUES (?, ?)",
                (sub, department)
            )
            print(f"Added: {sub} — {department}")
        else:
            print(f"Already exists: {sub} — {department}")


conn.commit()
conn.close()

print("subs added successfully")

