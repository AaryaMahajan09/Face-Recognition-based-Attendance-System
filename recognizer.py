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

RUN_CAMERA =False

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

    frame = cv2.resize(frame, (640, 480))  # 🔥 ADD

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = detector.detect_faces(rgb)

    print("Faces detected:", len(faces))  # DEBUG

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

        if min_distance < 0.75:
            name = known_names[index]
            reg_no = known_reg_nos[index]
            color = (0, 255, 0)
        else:
            name = "Unknown"
            reg_no = None
            color = (0, 0, 255)

        results.append((x, y, w, h, name, reg_no, color))

    return results


# 🔹 Mark attendance in DB
def mark_attendance_db(prn, department):

    conn = get_connection()
    cur = conn.cursor()

    # get user_id
    cur.execute("""
    SELECT users.id
    FROM users
    JOIN students ON users.id = students.user_id
    WHERE students.prn = ?
    """,(prn,))

    user = cur.fetchone()
    if not user:
        conn.close()
        return

    user_id = user["id"]

    # get active lecture
    cur.execute("""
    SELECT lecture_id, subject, staff_name
    FROM lectures
    WHERE department = ? AND is_active = 1
    """,(department,))

    lecture = cur.fetchone()
    if not lecture:
        conn.close()
        return

    lecture_id = lecture["lecture_id"]

    # prevent duplicate
    cur.execute("""
    SELECT 1 FROM attendance
    WHERE user_id = ? AND lecture_id = ?
    """,(user_id, lecture_id))

    if cur.fetchone():
        conn.close()
        return

    # insert attendance
    cur.execute("""
    INSERT INTO attendance
    (user_id, lecture_id, subject, staff_name, date, time, status)
    VALUES (?, ?, ?, ?, date('now','localtime'), time('now','localtime'), 'Present')
    """,(user_id, lecture_id, lecture["subject"], lecture["staff_name"]))

    conn.commit()
    conn.close()

    print(f"{prn} marked present ✅")


# 🔹 Start camera attendance
def start_face_attendance(department):

    global RUN_CAMERA
    RUN_CAMERA = True

    known_embeddings, known_names, known_reg_nos = load_embeddings()

    cap = cv2.VideoCapture(0)

    marked_students = set()

    print("📷 Face attendance started...")

    while RUN_CAMERA:
        ret, frame = cap.read()
        if not ret:
            break

        results = recognize(frame, known_embeddings, known_names, known_reg_nos)

        for (x, y, w, h, name, reg_no, color) in results:

            cv2.rectangle(frame, (x,y), (x+w,y+h), color, 2)
            cv2.putText(frame, name, (x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # 🔥 Auto mark attendance
            if reg_no and reg_no not in marked_students:
                mark_attendance_db(reg_no, department)
                marked_students.add(reg_no)
                time.sleep(1)   # prevent spam

        cv2.imshow("Face Attendance", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

        time.sleep(0.5)



    cap.release()
    cv2.destroyAllWindows()

    print("Camera Stopped")

def stop_camera():
    global RUN_CAMERA
    RUN_CAMERA =False