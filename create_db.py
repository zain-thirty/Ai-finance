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
<<<<<<< HEAD

def add_user(username, password, email):
    # Connect to SQLite database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        # Insert user into the table with default 'not approved' status
        cursor.execute('''
            INSERT INTO users (username, password, email, approved)
            VALUES (?, ?, ?, 'not approved')
        ''', (username, hashed_password, email))

        # Commit the transaction
        conn.commit()
        print('User added successfully!')

    except sqlite3.IntegrityError as e:
        print(f'Error occurred: {e}')
    
    finally:
        # Close the connection
        conn.close()
=======
>>>>>>> c2c588c28adcd4c7d3d2340d1faec53592fc79c4

if __name__ == '__main__':
    create_db()

