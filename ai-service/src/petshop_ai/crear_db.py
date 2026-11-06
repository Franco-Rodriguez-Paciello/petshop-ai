# crear_db.py — crea la base de datos del pet shop con datos de ejemplo
import sqlite3
from datetime import date, timedelta

from petshop_ai.config import get_settings


def crear_db(ruta: str | None = None) -> None:
    conexion = sqlite3.connect(ruta or get_settings().petshop_db)
    cursor = conexion.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS acciones_pendientes;
    DROP TABLE IF EXISTS pedidos;
    DROP TABLE IF EXISTS clientes;
    DROP TABLE IF EXISTS productos;

    CREATE TABLE productos (
        producto_id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        precio_usd REAL NOT NULL,
        stock INTEGER NOT NULL
    );

    CREATE TABLE clientes (
        cliente_id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE
    );

    CREATE TABLE pedidos (
        pedido_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id TEXT NOT NULL REFERENCES clientes(cliente_id),
        producto_id TEXT NOT NULL REFERENCES productos(producto_id),
        fecha_pedido TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'completado'    -- 'completado' | 'devuelto'
    );

    -- Acciones que el agente propone y que solo el cliente puede confirmar (human-in-the-loop)
    CREATE TABLE acciones_pendientes (
        accion_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id TEXT NOT NULL REFERENCES clientes(cliente_id),
        tipo TEXT NOT NULL,                           -- 'devolucion'
        pedido_id INTEGER NOT NULL REFERENCES pedidos(pedido_id),
        estado TEXT NOT NULL DEFAULT 'pendiente'      -- 'pendiente' | 'confirmada' | 'cancelada'
    );
    """)

    cursor.executemany(
        "INSERT INTO productos VALUES (?, ?, ?, ?)",
        [
            ("AL-101", "Alimento Premium para Perros 15kg", 45.99, 25),
            ("JU-201", "Juguete mordillo interactivo", 19.99, 40),
            ("AC-301", "Collar ajustable con correa reflectante", 14.50, 30),
            ("SN-401", "Snacks naturales de pollo 250g", 6.99, 60),
        ],
    )

    cursor.executemany(
        "INSERT INTO clientes VALUES (?, ?, ?)",
        [
            ("C-001", "María Gómez", "maria@example.com"),
            ("C-002", "Carlos Ruiz", "carlos@example.com"),
        ],
    )

    # Fechas RELATIVAS a hoy, para que las demos y los tests funcionen siempre
    hace_10_dias = (date.today() - timedelta(days=10)).isoformat()
    hace_45_dias = (date.today() - timedelta(days=45)).isoformat()

    cursor.executemany(
        "INSERT INTO pedidos (cliente_id, producto_id, fecha_pedido, estado) VALUES (?, ?, ?, ?)",
        [
            ("C-001", "JU-201", hace_10_dias, "completado"),  # id 1: devolución ELEGIBLE
            ("C-001", "AL-101", hace_45_dias, "completado"),  # id 2: NO elegible (fuera de 30 días)
            ("C-002", "AC-301", hace_10_dias, "devuelto"),  # id 3: ya devuelto
            ("C-002", "SN-401", hace_10_dias, "completado"),  # id 4: elegible, pero es de Carlos
        ],
    )

    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    crear_db()
    print("Base de datos creada con datos de ejemplo y fechas relativas")
