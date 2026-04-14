from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
print("VERSION NUEVA 123")
@app.route("/test")
def test():
    return "FUNCIONA"
app.secret_key = "clave123"

def get_db():
    return sqlite3.connect("contabilidad.db")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["password"]

        db = get_db()
        u = db.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (user,password)).fetchone()

        if u:
            session["user_id"] = u[0]
            return redirect("/dashboard")
        else:
            return "Error login"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    db = get_db()

    clientes = db.execute(
    "SELECT * FROM clientes WHERE usuario_id=?",
    (session["user_id"],)
).fetchall()
    transacciones = db.execute(
    "SELECT * FROM transacciones WHERE usuario_id=?",
    (session["user_id"],)
).fetchall()

    return render_template("dashboard.html", clientes=clientes, transacciones=transacciones)

@app.route("/cliente", methods=["POST"])
def cliente():
    db = get_db()
    db.execute(
    "INSERT INTO clientes (nombre, usuario_id) VALUES (?, ?)",
    (request.form["nombre"], session["user_id"])
)
    db.commit()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
@app.route("/crear_admin")
def crear_admin():
    db = get_db()
    db.execute("INSERT OR IGNORE INTO usuarios (id, username, password) VALUES (1, 'admin','1234')")
    db.commit()
    return "Usuario creado"
@app.route("/init_db")
def init_db():
    db = get_db()

    db.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, nombre TEXT)")

    db.execute("""
    CREATE TABLE IF NOT EXISTS transacciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descripcion TEXT,
        monto REAL,
        fecha TEXT
    )
    """)

    db.commit()
    return "Base de datos lista"
if __name__ == "__main__":
    app.run()
