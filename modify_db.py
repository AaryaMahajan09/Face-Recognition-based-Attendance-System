import sqlite3
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random
import numpy as np

DB_NAME = "database.db"
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()



# cur.execute("""
# DELETE FROM embeddings
# WHERE user_id = '5';""")
# conn.commit()
# conn.close()


# cur.execute("""
# UPDATE embeddings
# SET name = 'Jainam Parmar'
# WHERE name = 'Papa hu mai papa';""")
# conn.commit()
# conn.close()




#### to see data in pickle
# import pickle

# path = "image_data/embeddings.pkl"

# with open(path, "rb") as f:
#     data = pickle.load(f)

# for i in range(len(data["reg_nos"])):
#     print(f"{i+1}. Name: {data['names'][i]} | PRN: {data['reg_nos'][i]}")