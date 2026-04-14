import sqlite3

db = sqlite3.connect("contabilidad.db")

# 🔹 TABLA USUARIOS
db.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# 🔹 TABLA CLIENTES
db.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    usuario_id INTEGER
)
""")

# 🔹 TABLA PROVEEDORES
db.execute("""
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    usuario_id INTEGER
)
""")

# 🔹 TABLA TRANSACCIONES
db.execute("""
CREATE TABLE IF NOT EXISTS transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    descripcion TEXT,
    monto REAL,
    fecha TEXT,
    usuario_id INTEGER
)
""")

db.commit()
db.close()

print("Base de datos creada correctamente")
