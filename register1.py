import os
import cv2
import json
import numpy as np
from keras_facenet import FaceNet
from mtcnn import MTCNN
from database import get_connection

DATASET_PATH = "image_data"

embedder = FaceNet()
detector = MTCNN()

def register_student(user_id, name, prn, image):

    conn = get_connection()
    cur = conn.cursor()

    # check already registered
    cur.execute("""
        SELECT image_path FROM students
        WHERE user_id = ?
    """, (user_id,))
    existing = cur.fetchone()

    if existing and existing["image_path"]:
        conn.close()
        return "Face already registered"

    # save image
    os.makedirs(DATASET_PATH, exist_ok=True)
    image_path = os.path.join(DATASET_PATH, f"{prn}.jpg")
    cv2.imwrite(image_path, image)

    # detect face
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb)

    if not faces:
        conn.close()
        return "No face detected. Please retake in good lighting."

    x, y, w, h = faces[0]['box']
    x, y = abs(x), abs(y)
    face = rgb[y:y+h, x:x+w]

    if face.size == 0:
        conn.close()
        return "Face crop failed. Try again."

    face = cv2.resize(face, (160, 160))

    # generate average embedding
    embeddings_list = []
    for _ in range(5):
        emb = embedder.embeddings([face])[0]
        embeddings_list.append(emb)

    avg_embedding = np.mean(embeddings_list, axis=0)

    # ✅ store in DB instead of pkl
    embedding_json = json.dumps(avg_embedding.tolist())

    # check if embedding already exists for this prn
    cur.execute("SELECT id FROM embeddings WHERE prn = ?", (prn,))
    existing_emb = cur.fetchone()

    if existing_emb:
        # update existing
        cur.execute("""
            UPDATE embeddings
            SET embedding = ?, name = ?
            WHERE prn = ?
        """, (embedding_json, name, prn))
    else:
        # insert new
        cur.execute("""
            INSERT INTO embeddings (user_id, prn, name, embedding)
            VALUES (?, ?, ?, ?)
        """, (user_id, prn, name, embedding_json))

    # update students image path
    cur.execute("""
        UPDATE students SET image_path = ?
        WHERE user_id = ?
    """, (image_path, user_id))

    conn.commit()
    conn.close()

    print(f"✅ Registered: {name} ({prn})")
    return "Registration Successful"