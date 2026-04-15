from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "clave123"

print("VERSION PRO FINAL")

def get_db():
    return sqlite3.connect("contabilidad.db")


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["password"]

        db = get_db()
        u = db.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?",
            (user, password)
        ).fetchone()

        if u:
            session["user_id"] = u[0]
            return redirect("/dashboard")
        else:
            return "Error login"

    return render_template("login.html")


# REGISTRO (MULTIUSUARIO)
@app.route("/registro", methods=["GET","POST"])
def registro():
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["password"]

        db = get_db()
        db.execute(
            "INSERT INTO usuarios (username, password) VALUES (?, ?)",
            (user, password)
        )
        db.commit()

        return redirect("/")

    return render_template("registro.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    clientes = db.execute(
        "SELECT * FROM clientes WHERE usuario_id=?",
        (session["user_id"],)
    ).fetchall()

    proveedores = db.execute(
        "SELECT * FROM proveedores WHERE usuario_id=?",
        (session["user_id"],)
    ).fetchall()

    bancos = db.execute(
        "SELECT * FROM bancos WHERE usuario_id=?",
        (session["user_id"],)
    ).fetchall()

    transacciones = db.execute(
        "SELECT * FROM transacciones WHERE usuario_id=?",
        (session["user_id"],)
    ).fetchall()

    ingresos = db.execute(
        "SELECT COALESCE(SUM(monto),0) FROM transacciones WHERE tipo='ingreso' AND usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    gastos = db.execute(
        "SELECT COALESCE(SUM(monto),0) FROM transacciones WHERE tipo='gasto' AND usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    utilidad = ingresos - gastos

    return render_template(
        "dashboard.html",
        clientes=clientes,
        proveedores=proveedores,
        bancos=bancos,
        transacciones=transacciones,
        total_ingresos=ingresos,
        total_gastos=gastos,
        utilidad=utilidad
    )


# CLIENTE
@app.route("/cliente", methods=["POST"])
def cliente():
    db = get_db()
    db.execute(
        "INSERT INTO clientes (nombre, usuario_id) VALUES (?, ?)",
        (request.form["nombre"], session["user_id"])
    )
    db.commit()
    return redirect("/dashboard")


# PROVEEDOR
@app.route("/proveedor", methods=["POST"])
def proveedor():
    db = get_db()
    db.execute(
        "INSERT INTO proveedores (nombre, usuario_id) VALUES (?, ?)",
        (request.form["nombre"], session["user_id"])
    )
    db.commit()
    return redirect("/dashboard")


# BANCO
@app.route("/banco", methods=["POST"])
def banco():
    db = get_db()
    db.execute(
        "INSERT INTO bancos (nombre, saldo, usuario_id) VALUES (?, ?, ?)",
        (request.form["nombre"], request.form["saldo"], session["user_id"])
    )
    db.commit()
    return redirect("/dashboard")


# TRANSACCION
@app.route("/transaccion", methods=["POST"])
def transaccion():
    db = get_db()

    tipo = request.form["tipo"]
    descripcion = request.form["descripcion"]
    monto = float(request.form["monto"])
    fecha = request.form["fecha"]
    banco_id = request.form["banco"]

    db.execute("""
        INSERT INTO transacciones (tipo, descripcion, monto, fecha, usuario_id)
        VALUES (?, ?, ?, ?, ?)
    """, (tipo, descripcion, monto, fecha, session["user_id"]))

    if tipo == "ingreso":
        db.execute("UPDATE bancos SET saldo = saldo + ? WHERE id=?", (monto, banco_id))
    else:
        db.execute("UPDATE bancos SET saldo = saldo - ? WHERE id=?", (monto, banco_id))

    db.commit()
    return redirect("/dashboard")


# EXPORTAR
@app.route("/exportar")
def exportar():
    db = get_db()
    data = db.execute(
        "SELECT tipo, descripcion, monto, fecha FROM transacciones WHERE usuario_id=?",
        (session["user_id"],)
    ).fetchall()

    def generar():
        yield "tipo,descripcion,monto,fecha\n"
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]}\n"

    return Response(generar(), mimetype="text/csv")


# BALANCE PRO
@app.route("/balance")
def balance():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    activos = db.execute(
        "SELECT COALESCE(SUM(saldo),0) FROM bancos WHERE usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    ingresos = db.execute(
        "SELECT COALESCE(SUM(monto),0) FROM transacciones WHERE tipo='ingreso' AND usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    gastos = db.execute(
        "SELECT COALESCE(SUM(monto),0) FROM transacciones WHERE tipo='gasto' AND usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    patrimonio = ingresos - gastos
    pasivos = 0

    return render_template(
        "balance.html",
        activos=activos,
        pasivos=pasivos,
        patrimonio=patrimonio
    )


# REPORTES (ESTADO RESULTADOS)
@app.route("/reportes")
def reportes():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    ingresos = db.execute("""
        SELECT descripcion, SUM(monto)
        FROM transacciones
        WHERE tipo='ingreso' AND usuario_id=?
        GROUP BY descripcion
    """, (session["user_id"],)).fetchall()

    gastos = db.execute("""
        SELECT descripcion, SUM(monto)
        FROM transacciones
        WHERE tipo='gasto' AND usuario_id=?
        GROUP BY descripcion
    """, (session["user_id"],)).fetchall()

    total_ingresos = sum([i[1] for i in ingresos])
    total_gastos = sum([g[1] for g in gastos])
    utilidad = total_ingresos - total_gastos

    return render_template(
        "reportes.html",
        ingresos=ingresos,
        gastos=gastos,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        utilidad=utilidad
    )


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# RESET DB (CORREGIDO)
@app.route("/reset_db")
def reset_db():
    if os.path.exists("contabilidad.db"):
        os.remove("contabilidad.db")

    db = get_db()

    db.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
    db.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, usuario_id INTEGER)")
    db.execute("CREATE TABLE proveedores (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, usuario_id INTEGER)")
    db.execute("CREATE TABLE bancos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, saldo REAL, usuario_id INTEGER)")

    db.execute("""
    CREATE TABLE transacciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descripcion TEXT,
        monto REAL,
        fecha TEXT,
        usuario_id INTEGER
    )
    """)

    db.commit()
    return "Base reiniciada OK"


# CREAR ADMIN
@app.route("/crear_admin")
def crear_admin():
    db = get_db()
    db.execute("DELETE FROM usuarios")
    db.execute("INSERT INTO usuarios (username, password) VALUES ('admin','1234')")
    db.commit()
    return "admin creado"


if __name__ == "__main__":
    app.run()
