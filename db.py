import sqlite3

# Function to create a connection to the database
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('ship_infoo.db')
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn
