import sqlite3
import os

DB_PATH = os.path.join('data', 'jobs.db')

def migrate_jobs_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns_to_add = {
        'duration_seconds': 'REAL',
        'language_detected': 'TEXT',
        'error_message': 'TEXT',
        'completed_at': 'TIMESTAMP'
    }

    for column_name, column_type in columns_to_add.items():
        try:
            cursor.execute(f'ALTER TABLE jobs ADD COLUMN {column_name} {column_type}')
            print(f'Added column: {column_name}')
        except sqlite3.OperationalError as e:
            if f'duplicate column name: {column_name}' in str(e):
                print(f'Column {column_name} already exists, skipping.')
            else:
                raise e

    conn.commit()
    conn.close()
    print('Migration complete!')

if __name__ == '__main__':
    migrate_jobs_table()
