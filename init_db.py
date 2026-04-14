import sqlite3

db = sqlite3.connect("contabilidad.db")

db.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
db.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT)")

db.commit()