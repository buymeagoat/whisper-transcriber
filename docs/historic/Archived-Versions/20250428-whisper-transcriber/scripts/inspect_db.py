import sqlite3
import os

# Always locate the DB relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Go up one level
DB_PATH = os.path.join(BASE_DIR, 'data', 'jobs.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

for table in tables:
    print(f"\nSchema for table {table[0]}:")
    cursor.execute(f"PRAGMA table_info({table[0]});")
    columns = cursor.fetchall()
    for column in columns:
        print(column)

conn.close()
