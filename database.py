import sqlite3

DB_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    
    return conn


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # STUDENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        prn TEXT UNIQUE,
        image_path TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # LECTURES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lectures(
        lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        staff_name TEXT,
        department TEXT,
        start_time TEXT,
        end_time TEXT,
        is_active INTEGER
    )
    """)

    # ATTENDANCE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER ,
        lecture_id INTEGER,
        subject TEXT,
        staff_name TEXT,
        department TEXT,
        date TEXT,
        time TEXT,
        status TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
    )
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS unique_attendance
    ON attendance(user_id, lecture_id)
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        department TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS embeddings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        prn TEXT,
        name TEXT,
        embedding TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()