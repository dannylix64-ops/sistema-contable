from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import stripe

app = Flask(__name__)
app.secret_key = "clave123"

# 🔑 STRIPE (REEMPLAZA CON TU CLAVE REAL)
stripe.api_key = "TU_CLAVE_SECRETA"


def get_db():
    return sqlite3.connect("contabilidad.db")


# 🔹 LOGIN
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


# 🔹 DASHBOARD
@app.route("/dashboard")
def dashboard():
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

    total_ingresos = db.execute(
        "SELECT COALESCE(SUM(monto),0) FROM transacciones WHERE tipo='ingreso' AND usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    total_gastos = db.execute(
        "SELECT COALESCE(SUM(monto),0) FROM transacciones WHERE tipo='gasto' AND usuario_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    utilidad = total_ingresos - total_gastos

    return render_template(
        "dashboard.html",
        clientes=clientes,
        proveedores=proveedores,
        bancos=bancos,
        transacciones=transacciones,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        utilidad=utilidad
    )


# 🔹 CLIENTE
@app.route("/cliente", methods=["POST"])
def cliente():
    db = get_db()

    db.execute(
        "INSERT INTO clientes (nombre, usuario_id) VALUES (?, ?)",
        (request.form["nombre"], session["user_id"])
    )

    db.commit()
    return redirect("/dashboard")


# 🔹 PROVEEDOR
@app.route("/proveedor", methods=["POST"])
def proveedor():
    db = get_db()

    db.execute(
        "INSERT INTO proveedores (nombre, usuario_id) VALUES (?, ?)",
        (request.form["nombre"], session["user_id"])
    )

    db.commit()
    return redirect("/dashboard")


# 🔹 BANCO
@app.route("/banco", methods=["POST"])
def banco():
    db = get_db()

    db.execute(
        "INSERT INTO bancos (nombre, saldo, usuario_id) VALUES (?, ?, ?)",
        (
            request.form["nombre"],
            request.form["saldo"],
            session["user_id"]
        )
    )

    db.commit()
    return redirect("/dashboard")


# 🔹 TRANSACCION (CON SALDO AUTOMÁTICO)
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

    # 💰 ACTUALIZAR SALDO AUTOMÁTICO
    if tipo == "ingreso":
        db.execute("UPDATE bancos SET saldo = saldo + ? WHERE id=?", (monto, banco_id))
    else:
        db.execute("UPDATE bancos SET saldo = saldo - ? WHERE id=?", (monto, banco_id))

    db.commit()
    return redirect("/dashboard")


# 🔹 EXPORTAR CSV
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

    return Response(
        generar(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=transacciones.csv"}
    )


# 🔹 PAGO STRIPE
@app.route("/pagar")
def pagar():
    session_stripe = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Sistema Contable Pro',
                },
                'unit_amount': 1000,  # $10
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://sistema-contable-eigb.onrender.com/dashboard',
        cancel_url='https://sistema-contable-eigb.onrender.com/',
    )

    return redirect(session_stripe.url)


# 🔹 LANDING
@app.route("/landing")
def landing():
    return render_template("landing.html")


# 🔹 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 🔹 CREAR ADMIN
@app.route("/crear_admin")
def crear_admin():
    db = get_db()

    db.execute("""
        INSERT OR IGNORE INTO usuarios (id, username, password)
        VALUES (1, 'admin', '1234')
    """)

    db.commit()
    return redirect("/")


# 🔹 RESET DB
@app.route("/reset_db")
def reset_db():
    db = get_db()

    db.execute("DROP TABLE IF EXISTS usuarios")
    db.execute("DROP TABLE IF EXISTS clientes")
    db.execute("DROP TABLE IF EXISTS proveedores")
    db.execute("DROP TABLE IF EXISTS bancos")
    db.execute("DROP TABLE IF EXISTS transacciones")

    db.execute("""
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    db.execute("""
    CREATE TABLE clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        usuario_id INTEGER
    )
    """)

    db.execute("""
    CREATE TABLE proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        usuario_id INTEGER
    )
    """)

    db.execute("""
    CREATE TABLE bancos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        saldo REAL,
        usuario_id INTEGER
    )
    """)

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
    return redirect("/")


# 🔹 MAIN
if __name__ == "__main__":
    app.run()
