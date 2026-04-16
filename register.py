import os
import cv2
import pickle
import numpy as np
import sqlite3
from keras_facenet import FaceNet
from mtcnn import MTCNN
from database import get_connection, create_tables

DATASET_PATH = "image_data/face_img"
EMBEDDING_PATH = "image_data/embeddings.pkl"

embedder = FaceNet()
detector = MTCNN()


def register_student(user_id,name, prn, image):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT image_path FROM students
    WHERE user_id = ?
    """, (user_id,))

    existing = cur.fetchone()

    if existing and existing["image_path"]:
        conn.close()
        return "Face already registered"
    
    
    os.makedirs(DATASET_PATH, exist_ok=True)

    image_path = os.path.join(DATASET_PATH, f"{prn}.jpg")
    cv2.imwrite(image_path, image)

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb)

    if not faces:
        conn.close()
        return "No face detected. Please retake in good lighting."

    x, y, w, h = faces[0]['box']
    x, y = abs(x), abs(y)

    face = rgb[y:y+h, x:x+w]
    face = cv2.resize(face, (160, 160))

    # Average 5 embeddings
    embeddings_list = []
    for _ in range(5):
        emb = embedder.embeddings([face])[0]
        embeddings_list.append(emb)

    avg_embedding = np.mean(embeddings_list, axis=0)

    if os.path.exists(EMBEDDING_PATH):
        with open(EMBEDDING_PATH, "rb") as f:
            data = pickle.load(f)
        embeddings = list(data["embeddings"])
        names = data["names"]
        reg_nos = data["reg_nos"]
    else:
        embeddings = []
        names = []
        reg_nos = []

    if prn in reg_nos:
        idx = reg_nos.index(prn)
        embeddings[idx] = avg_embedding  # overwrite existing
        names[idx] = name
    else:
        embeddings.append(avg_embedding)  # fresh entry
        names.append(name)
        reg_nos.append(prn)

    with open(EMBEDDING_PATH, "wb") as f:
        pickle.dump({
            "embeddings": np.array(embeddings),
            "names": names,
            "reg_nos": reg_nos
        }, f)


    

    cur.execute("""
        UPDATE students 
        SET image_path =? 
        WHERE user_id =?
    """, (image_path,user_id))

    conn.commit()
    conn.close()

    return "Registration Successful"