import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="test",
        autocommit=True   # evita lock se ti dimentichi il commit
    )
    return conn