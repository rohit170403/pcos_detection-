import sqlite3

def init_db():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_responses;')
        conn.commit()  # Ensure that changes are saved
        print("All records deleted.")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

init_db()
