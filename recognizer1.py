import cv2
import numpy as np
import json
import os
import time

from keras_facenet import FaceNet
from mtcnn import MTCNN
from database import get_connection

embedder = None
detector = None

RUN_CAMERA = False

def get_models():
    global embedder, detector
    if embedder is None:
        embedder = FaceNet()
    if detector is None:
        detector = MTCNN()
    return embedder, detector


# ✅ Load embeddings from DB instead of pkl
def load_embeddings():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT prn, name, embedding FROM embeddings")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("⚠️ No embeddings found in DB")
        return np.array([]), [], []

    embeddings = []
    names = []
    reg_nos = []

    for row in rows:
        emb = np.array(json.loads(row["embedding"]))
        embeddings.append(emb)
        names.append(row["name"])
        reg_nos.append(row["prn"])

    print(f"✅ Loaded {len(names)} embeddings from DB")
    return np.array(embeddings), names, reg_nos


def recognize(frame, known_embeddings, known_names, known_reg_nos):

    if known_embeddings is None or len(known_embeddings) == 0:
        return []

    embedder, detector = get_models()

    frame = cv2.resize(frame, (640, 480))
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb)

    print(f"🔍 Faces detected: {len(faces)}")

    results = []

    for face_data in faces:
        x, y, w, h = face_data['box']
        x, y = abs(x), abs(y)
        face_crop = rgb[y:y+h, x:x+w]

        if face_crop.size == 0:
            continue

        try:
            face_crop = cv2.resize(face_crop, (160, 160))
        except Exception as e:
            print("Resize error:", e)
            continue

        embedding = embedder.embeddings([face_crop])[0]
        distances = np.linalg.norm(known_embeddings - embedding, axis=1)
        min_distance = np.min(distances)
        index = np.argmin(distances)

        if min_distance < 0.75:
            name = known_names[index]
            reg_no = known_reg_nos[index]
            color = (0, 255, 0)
            print(f"✅ Recognized: {name} ({reg_no}) dist={min_distance:.3f}")
        else:
            name = "Unknown"
            reg_no = None
            color = (0, 0, 255)
            print(f"❓ Unknown face dist={min_distance:.3f}")

        results.append((x, y, w, h, name, reg_no, color))

    return results


def mark_attendance_db(prn, department):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT users.id FROM users
        JOIN students ON users.id = students.user_id
        WHERE students.prn = ?
    """, (prn,))

    user = cur.fetchone()
    if not user:
        conn.close()
        return

    user_id = user["id"]

    cur.execute("""
        SELECT lecture_id, subject, staff_name FROM lectures
        WHERE department = ? AND is_active = 1
    """, (department,))

    lecture = cur.fetchone()
    if not lecture:
        conn.close()
        return

    lecture_id = lecture["lecture_id"]

    cur.execute("""
        SELECT 1 FROM attendance
        WHERE user_id = ? AND lecture_id = ?
    """, (user_id, lecture_id))

    if cur.fetchone():
        conn.close()
        return

    cur.execute("""
        INSERT INTO attendance
        (user_id, lecture_id, subject, staff_name,department, date, time, status)
        VALUES (?, ?, ?, ? , ?, date('now','localtime'), time('now','localtime'), 'Present')
    """, (user_id, lecture_id, lecture["subject"], lecture["staff_name"], department))

    conn.commit()
    conn.close()
    print(f"✅ Attendance marked for PRN={prn}")


def stop_camera():
    global RUN_CAMERA
    RUN_CAMERA = False