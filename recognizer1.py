import cv2
import numpy as np
import pickle
import os
import time

from keras_facenet import FaceNet
from mtcnn import MTCNN
from database import get_connection


EMBEDDING_PATH = "image_data/embeddings.pkl"

embedder = FaceNet()
detector = MTCNN()

RUN_CAMERA = False


# 🔹 Load embeddings
def load_embeddings():
    if not os.path.exists(EMBEDDING_PATH):
        return [], [], []

    with open(EMBEDDING_PATH, "rb") as f:
        data = pickle.load(f)

    return np.array(data["embeddings"]), data["names"], data["reg_nos"]


# 🔹 Recognize faces
def recognize(frame, known_embeddings, known_names, known_reg_nos):

    if len(known_embeddings) == 0:
        return []

    frame = cv2.resize(frame, (640, 480))
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = detector.detect_faces(rgb)

    results = []

    for face_data in faces:
        x, y, w, h = face_data['box']
        x, y = abs(x), abs(y)

        face_crop = rgb[y:y+h, x:x+w]

        if face_crop.size == 0:
            continue

        try:
            face_crop = cv2.resize(face_crop, (160, 160))
        except:
            continue

        embedding = embedder.embeddings([face_crop])[0]

        distances = np.linalg.norm(known_embeddings - embedding, axis=1)

        min_distance = np.min(distances)
        index = np.argmin(distances)

        if min_distance < 0.70:
            name = known_names[index]
            reg_no = known_reg_nos[index]
        else:
            name = "Unknown"
            reg_no = None

        results.append((x, y, w, h, name, reg_no))

    return results


# 🔹 Mark attendance in DB
def mark_attendance_db(prn, department):

    conn = get_connection()
    cur = conn.cursor()

    # 🔹 Get user_id
    cur.execute("""
    SELECT users.id
    FROM users
    JOIN students ON users.id = students.user_id
    WHERE students.prn = ?
    """, (prn,))

    user = cur.fetchone()
    if not user:
        conn.close()
        return "User not found ❌"

    user_id = user["id"]

    # 🔹 Get active lecture
    cur.execute("""
    SELECT lecture_id, subject, staff_name
    FROM lectures
    WHERE department = ? AND is_active = 1
    """, (department,))

    lecture = cur.fetchone()
    if not lecture:
        conn.close()
        return "No active lecture ❌"

    lecture_id = lecture["lecture_id"]

    # 🔹 Prevent duplicate attendance
    cur.execute("""
    SELECT 1 FROM attendance
    WHERE user_id = ? AND lecture_id = ?
    """, (user_id, lecture_id))

    if cur.fetchone():
        conn.close()
        return "Already marked ⚠️"

    # 🔹 Insert attendance
    cur.execute("""
    INSERT INTO attendance
    (user_id, lecture_id, subject, staff_name, date, time, status)
    VALUES (?, ?, ?, ?, date('now','localtime'), time('now','localtime'), 'Present')
    """, (user_id, lecture_id, lecture["subject"], lecture["staff_name"]))

    conn.commit()
    conn.close()

    print(f"{prn} marked present ✅")

    return "Attendance marked ✅"

# 🔥 MAIN FUNCTION
def start_face_attendance(department, logged_in_prn):

    global RUN_CAMERA
    RUN_CAMERA = True

    known_embeddings, known_names, known_reg_nos = load_embeddings()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera not accessible")
        return

    last_mark_time = {}   # 🔥 cooldown dictionary

    print("📷 Face attendance started...")

    while RUN_CAMERA:

        ret, frame = cap.read()
        if not ret:
            break

        results = recognize(frame, known_embeddings, known_names, known_reg_nos)

        current_time = time.time()

        if len(results)>1:
            cv2.putText(frame, "Multiple Faces Detected",
                        (20,50),cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255),3)
            
            cv2.imshow("Face Ateendance",frame)
            continue

        for (x, y, w, h, name, reg_no) in results:

            # 🔐 Authorization check
            if reg_no == logged_in_prn:
                label = f"{name} (Authorized)"
                color = (0, 255, 0)
            
            elif reg_no is None:
                label = "Unknown Face"
                color = (0, 0, 255)
            else:
                label = "Unauthorized"
                color = (0, 0, 255)

            # Draw rectangle + label
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # ✅ Mark attendance ONLY for logged-in user
            if reg_no == logged_in_prn:

                if reg_no not in last_mark_time or current_time - last_mark_time[reg_no] > 5:

                    mark_attendance_db(reg_no, department)
                    last_mark_time[reg_no] = current_time

                    print(f"{reg_no} marked present ✅")

                    # 🔥 OPTIONAL: Stop after success
                    RUN_CAMERA = False

        cv2.imshow("Face Attendance", frame)

        # Press ESC to exit
        if cv2.waitKey(1) & 0xFF == 27:
            break

        time.sleep(0.3)

    cap.release()
    cv2.destroyAllWindows()

    print("Camera Stopped")


# 🔴 Stop camera manually
def stop_camera():
    global RUN_CAMERA
    RUN_CAMERA = False
