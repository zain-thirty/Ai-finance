import sqlite3
import bcrypt

def create_db():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create a table for user credentials, including the email and approved status fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            approved TEXT DEFAULT 'not approved'  -- New column with default value
        )
    ''')
    
    # Commit and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()

