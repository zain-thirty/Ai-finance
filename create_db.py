import sqlite3
import bcrypt

def create_db():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create a table for user credentials, including the new email field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    
    # Commit and close the connection
    conn.commit()
    conn.close()
def add_user(username, password, email):
    # Connect to SQLite database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        # Insert user into the table
        cursor.execute('''
            INSERT INTO users (username, password, email)
            VALUES (?, ?, ?)
        ''', (username, hashed_password, email))

        # Commit the transaction
        conn.commit()
        print('User added successfully!')

    except sqlite3.IntegrityError as e:
        print(f'Error occurred: {e}')
    
    finally:
        # Close the connection
        conn.close()

if __name__ == '__main__':
    create_db()
    add_user("abc", "123", "123@gmail.com")
