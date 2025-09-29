import mysql.connector
import bcrypt

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="test",
        autocommit=True   # evita lock se ti dimentichi il commit
    )
    return conn

def create_user():
    username = "utente"
    password_plain = "password"

    # genera l'hash bcrypt (salt automatico)
    hashed = bcrypt.hashpw(password_plain.encode(), bcrypt.gensalt())

    conn = get_connection()
    cursor = conn.cursor()

    insert_query = "INSERT INTO utenti (Nome, Password) VALUES (%s, %s)"
    cursor.execute(insert_query, (username, hashed.decode("utf-8")))

    cursor.close()
    conn.close()

    print(f"✅ Utente '{username}' creato con successo")

if __name__ == "__main__":
    create_user()