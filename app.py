from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = "secret123"

# 🔌 CONEXIÓN BD
def get_db():
    conn = sqlite3.connect("contabilidad.db")
    conn.row_factory = sqlite3.Row
    return conn

# 🧱 CREAR BD AUTOMÁTICA (IMPORTANTE PARA RENDER)
def init_db():
    conn = sqlite3.connect("contabilidad.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bancos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        saldo REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        banco_id INTEGER,
        descripcion TEXT,
        monto REAL,
        fecha TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nombre TEXT,
        tipo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        descripcion TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_diario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        diario_id INTEGER,
        cuenta_id INTEGER,
        debe REAL,
        haber REAL
    )
    """)

    # cuentas base
    cursor.execute("INSERT OR IGNORE INTO cuentas (id, codigo, nombre, tipo) VALUES (1,'1.1','Bancos','Activo')")
    cursor.execute("INSERT OR IGNORE INTO cuentas (id, codigo, nombre, tipo) VALUES (2,'4.1','Ingresos','Ingreso')")
    cursor.execute("INSERT OR IGNORE INTO cuentas (id, codigo, nombre, tipo) VALUES (3,'5.1','Gastos','Gasto')")

    conn.commit()
    conn.close()

# 🚀 INICIO DIRECTO (ELIMINA ERROR BAD REQUEST)
@app.route("/")
def inicio():
    return redirect("/dashboard")

# 📊 DASHBOARD
@app.route("/dashboard")
def dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.execute("SELECT * FROM proveedores")
    proveedores = cursor.fetchall()

    cursor.execute("SELECT * FROM bancos")
    bancos = cursor.fetchall()

    cursor.execute("SELECT * FROM transacciones")
    transacciones = cursor.fetchall()

    total_ingresos = sum(float(t["monto"]) for t in transacciones if t["tipo"] == "ingreso")
    total_gastos = sum(float(t["monto"]) for t in transacciones if t["tipo"] == "gasto")
    utilidad = total_ingresos - total_gastos

    return render_template("dashboard.html",
        clientes=clientes,
        proveedores=proveedores,
        bancos=bancos,
        transacciones=transacciones,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        utilidad=utilidad
    )

# 👥 CLIENTES
@app.route("/cliente", methods=["POST"])
def cliente():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nombre) VALUES (?)", (request.form["nombre"],))
    conn.commit()
    return redirect("/dashboard")

# 🏢 PROVEEDORES
@app.route("/proveedor", methods=["POST"])
def proveedor():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO proveedores (nombre) VALUES (?)", (request.form["nombre"],))
    conn.commit()
    return redirect("/dashboard")

# 🏦 BANCOS
@app.route("/banco", methods=["POST"])
def banco():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bancos (nombre, saldo) VALUES (?, ?)",
                   (request.form["nombre"], request.form["saldo"]))
    conn.commit()
    return redirect("/dashboard")

# 💳 TRANSACCIONES + DIARIO AUTOMÁTICO
@app.route("/transaccion", methods=["POST"])
def transaccion():
    conn = get_db()
    cursor = conn.cursor()

    tipo = request.form["tipo"]
    banco_id = request.form["banco"]
    descripcion = request.form["descripcion"]
    monto = float(request.form["monto"])
    fecha = request.form["fecha"]

    cursor.execute("""
    INSERT INTO transacciones (tipo, banco_id, descripcion, monto, fecha)
    VALUES (?, ?, ?, ?, ?)
    """, (tipo, banco_id, descripcion, monto, fecha))

    # cuentas
    cursor.execute("SELECT id FROM cuentas WHERE nombre='Bancos'")
    banco = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM cuentas WHERE nombre='Ingresos'")
    ingresos = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM cuentas WHERE nombre='Gastos'")
    gastos = cursor.fetchone()["id"]

    cursor.execute("INSERT INTO diario (fecha, descripcion) VALUES (?, ?)", (fecha, descripcion))
    diario_id = cursor.lastrowid

    if tipo == "ingreso":
        cursor.execute("INSERT INTO detalle_diario VALUES (NULL, ?, ?, ?, 0)", (diario_id, banco, monto))
        cursor.execute("INSERT INTO detalle_diario VALUES (NULL, ?, ?, 0, ?)", (diario_id, ingresos, monto))
    else:
        cursor.execute("INSERT INTO detalle_diario VALUES (NULL, ?, ?, ?, 0)", (diario_id, gastos, monto))
        cursor.execute("INSERT INTO detalle_diario VALUES (NULL, ?, ?, 0, ?)", (diario_id, banco, monto))

    conn.commit()
    return redirect("/dashboard")

# 📘 DIARIO
@app.route("/diario")
def diario():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT d.fecha, d.descripcion, c.nombre, dd.debe, dd.haber
    FROM detalle_diario dd
    JOIN diario d ON d.id = dd.diario_id
    JOIN cuentas c ON c.id = dd.cuenta_id
    ORDER BY d.fecha DESC
    """)

    datos = cursor.fetchall()
    return render_template("diario.html", datos=datos)

# 📊 BALANCE
@app.route("/balance")
def balance():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.tipo, SUM(dd.debe), SUM(dd.haber)
    FROM detalle_diario dd
    JOIN cuentas c ON c.id = dd.cuenta_id
    GROUP BY c.tipo
    """)

    datos = cursor.fetchall()

    activos = pasivos = patrimonio = 0

    for d in datos:
        saldo = (d[1] or 0) - (d[2] or 0)

        if d[0] == "Activo":
            activos += saldo
        elif d[0] == "Pasivo":
            pasivos += saldo
        elif d[0] == "Patrimonio":
            patrimonio += saldo

    return render_template("balance.html",
        activos=activos,
        pasivos=pasivos,
        patrimonio=patrimonio
    )

# 📈 RESULTADOS
@app.route("/resultados")
def resultados():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.tipo, SUM(dd.debe), SUM(dd.haber)
    FROM detalle_diario dd
    JOIN cuentas c ON c.id = dd.cuenta_id
    WHERE c.tipo IN ('Ingreso','Gasto')
    GROUP BY c.tipo
    """)

    datos = cursor.fetchall()

    ingresos = gastos = 0

    for d in datos:
        if d[0] == "Ingreso":
            ingresos += (d[2] or 0) - (d[1] or 0)
        elif d[0] == "Gasto":
            gastos += (d[1] or 0) - (d[2] or 0)

    utilidad = ingresos - gastos

    return render_template("resultados.html",
        ingresos=ingresos,
        gastos=gastos,
        utilidad=utilidad
    )

# 📥 EXPORTAR EXCEL
@app.route("/exportar")
def exportar():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transacciones", conn)
    archivo = "reporte.xlsx"
    df.to_excel(archivo, index=False)
    return send_file(archivo, as_attachment=True)

# 🚀 INICIAR BD SIEMPRE
init_db()
