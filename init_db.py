import sqlite3

db = sqlite3.connect("contabilidad.db")

db.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
db.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT)")

db.execute("""
CREATE TABLE transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    descripcion TEXT,
    monto REAL,
    fecha TEXT
)
""")

db.commit()
