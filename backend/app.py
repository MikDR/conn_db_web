from flask import Flask, request, render_template, jsonify, redirect, url_for
from db_config import get_connection
import bcrypt
import os
import pandas as pd
import mysql.connector

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def upload_to_db(path_file):
    df = pd.read_csv(path_file)

    # Connessione al DB (meglio se autocommit=True in get_connection)
    conn = get_connection()
    cursor = conn.cursor()
    print("Connesso al db")

    insert_query = """
        INSERT INTO dati (
            File, Iteration, Max_columns, Duration_w_all_Columns,
            Duration_w_max_columns, Num_op_w_all_columns, Num_op_w_max_columns
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    # Prepara tutti i valori come lista di tuple
    values = df[
        ["File", "Iteration", "Max_columns", "Duration_w_all_Columns",
         "Duration_w_max_columns", "Num_op_w_all_columns", "Num_op_w_max_columns"]
    ].where(pd.notnull(df), None).values.tolist()

    # Inserimento bulk
    cursor.executemany(insert_query, values)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ {len(values)} nuovi record inseriti nel database!")

@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")

@app.route("/main_page", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM utenti WHERE Nome=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user['Password'].encode()):
        # redirect GET con nome nella query string
        return redirect(url_for("main_page_get", nome=user['Nome']))
    else:
        return "<h3>Login fallito! Username o password errati.</h3>"

@app.route("/main_page", methods=["GET"])
def main_page_get():
    nome = request.args.get("nome", "Utente")
    return render_template("main_page.html", nome=nome)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "Nessun file selezionato"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "Nessun file selezionato"}), 400

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], "dati_combinati.csv")
    save_new_path = os.path.join(app.config['UPLOAD_FOLDER'], "new_dati.csv")

    # Se il file finale NON esiste o è vuoto → scriviamo tutto (compreso header)
    if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
        df = pd.read_csv(file)  # legge tutto normalmente
        df.to_csv(save_path, index=False, mode="w", header=True)
        df.to_csv(save_new_path, index=False, mode="w", header=True)  # sovrascrive sempre
    else:
        # Se esiste già → ignoriamo l’header del file caricato
        df = pd.read_csv(file, skiprows=1, header=None)
        
        # Otteniamo le colonne del file esistente
        existing_cols = pd.read_csv(save_path, nrows=0).columns.tolist()
        df.columns = existing_cols  # assegna le stesse colonne
        
        # Append senza duplicare header
        df.to_csv(save_path, index=False, mode="a", header=False)

        df.to_csv(save_new_path, index=False, mode="w", header=True)
    upload_to_db(save_new_path)

    return jsonify({"message": f"File {file.filename} aggiunto con successo alla collezione."})

if __name__ == "__main__":
    app.run(debug=True)
