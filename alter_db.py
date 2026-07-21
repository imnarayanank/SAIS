import sqlite3
import os

db_path = 'c:/Users/Admin/Desktop/LEARNABLE/backend/sais.db'
if not os.path.exists(db_path):
    print("Database not found")
else:
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("ALTER TABLE courses ADD COLUMN credits FLOAT DEFAULT 3.0;")
        c.execute("ALTER TABLE courses ADD COLUMN grade VARCHAR(5);")
        conn.commit()
        conn.close()
        print("Database altered successfully.")
    except Exception as e:
        print(f"Error: {e}")
