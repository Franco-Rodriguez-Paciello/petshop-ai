# servicios.py — reglas de negocio puras, sin LLM (el equivalente a tu capa de servicios en .NET).
# El cliente_id siempre llega del código que autenticó la request, nunca del modelo.
from datetime import date, timedelta

from petshop_ai import db

DIAS_VENTANA_DEVOLUCION = 30


class ErrorDeDominio(Exception):
    """Resultado de negocio esperable que el agente debe comunicar al cliente (los "404/409")."""


def listar_productos() -> list[dict]:
    return db.obtener_todos("SELECT * FROM productos ORDER BY producto_id")


def consultar_producto(producto_id: str) -> dict:
    producto = db.obtener_uno(
        "SELECT producto_id, nombre, precio_usd, stock FROM productos WHERE producto_id = ?",
        (producto_id.strip().upper(),),
    )
    if producto is None:
        raise ErrorDeDominio(f"No existe el producto {producto_id}.")
    return producto


def obtener_cliente(cliente_id: str) -> dict:
    cliente = db.obtener_uno("SELECT cliente_id, nombre, email FROM clientes WHERE cliente_id = ?", (cliente_id,))
    if cliente is None:
        raise PermissionError("Cliente no autenticado.")
    return cliente


def pedidos_del_cliente(cliente_id: str) -> list[dict]:
    return db.obtener_todos(
        """SELECT p.pedido_id, pr.nombre, pr.precio_usd, p.fecha_pedido, p.estado
           FROM pedidos p JOIN productos pr ON pr.producto_id = p.producto_id
           WHERE p.cliente_id = ? ORDER BY p.fecha_pedido DESC""",
        (cliente_id,),
    )


def _pedido_del_cliente(cliente_id: str, pedido_id: int) -> dict:
    if pedido_id <= 0:
        raise ValueError("El pedido_id debe ser un entero positivo.")
    pedido = db.obtener_uno(
        """SELECT p.pedido_id, p.cliente_id, p.fecha_pedido, p.estado, pr.nombre, pr.precio_usd
           FROM pedidos p JOIN productos pr ON pr.producto_id = p.producto_id
           WHERE p.pedido_id = ? AND p.cliente_id = ?""",
        (pedido_id, cliente_id),
    )
    if pedido is None:
        # Mismo mensaje exista o no el pedido: no revelamos pedidos de otros clientes
        raise ErrorDeDominio(f"No encontré el pedido {pedido_id} entre tus pedidos.")
    return pedido


def verificar_elegibilidad(pedido: dict, hoy: date | None = None) -> None:
    if pedido["estado"] == "devuelto":
        raise ErrorDeDominio(f"El pedido {pedido['pedido_id']} ya fue devuelto anteriormente.")
    fecha_pedido = date.fromisoformat(pedido["fecha_pedido"])
    fecha_limite = fecha_pedido + timedelta(days=DIAS_VENTANA_DEVOLUCION)
    if (hoy or date.today()) > fecha_limite:
        raise ErrorDeDominio(
            f"La devolución no es elegible: el pedido es del {fecha_pedido} "
            f"y la ventana de {DIAS_VENTANA_DEVOLUCION} días venció el {fecha_limite}."
        )


def solicitar_devolucion(cliente_id: str, pedido_id: int) -> dict:
    """Valida la devolución y crea una acción pendiente. NO la ejecuta: la confirma el cliente."""
    pedido = _pedido_del_cliente(cliente_id, pedido_id)
    verificar_elegibilidad(pedido)
    existente = db.obtener_uno(
        "SELECT accion_id FROM acciones_pendientes WHERE pedido_id = ? AND estado = 'pendiente'",
        (pedido_id,),
    )
    if existente:
        accion_id = existente["accion_id"]
    else:
        db.ejecutar(
            "INSERT INTO acciones_pendientes (cliente_id, tipo, pedido_id) VALUES (?, 'devolucion', ?)",
            (cliente_id, pedido_id),
        )
        accion_id = db.obtener_uno("SELECT MAX(accion_id) AS id FROM acciones_pendientes")["id"]
    return {
        "accion_id": accion_id,
        "tipo": "devolucion",
        "pedido_id": pedido_id,
        "producto": pedido["nombre"],
        "monto_usd": pedido["precio_usd"],
    }


def acciones_pendientes(cliente_id: str) -> list[dict]:
    return db.obtener_todos(
        """SELECT a.accion_id, a.tipo, a.pedido_id, pr.nombre AS producto, pr.precio_usd AS monto_usd
           FROM acciones_pendientes a
           JOIN pedidos p ON p.pedido_id = a.pedido_id
           JOIN productos pr ON pr.producto_id = p.producto_id
           WHERE a.cliente_id = ? AND a.estado = 'pendiente'""",
        (cliente_id,),
    )


def confirmar_accion(cliente_id: str, accion_id: int) -> str:
    """La ejecuta el cliente desde la UI (botón "Confirmar"), sin pasar por el LLM."""
    accion = db.obtener_uno(
        "SELECT * FROM acciones_pendientes WHERE accion_id = ? AND cliente_id = ? AND estado = 'pendiente'",
        (accion_id, cliente_id),
    )
    if accion is None:
        raise ErrorDeDominio(f"No hay una acción pendiente {accion_id} para confirmar.")

    pedido = _pedido_del_cliente(cliente_id, accion["pedido_id"])
    verificar_elegibilidad(pedido)  # se revalida: pudo cambiar algo entre la propuesta y la confirmación
    db.ejecutar("UPDATE pedidos SET estado = 'devuelto' WHERE pedido_id = ?", (pedido["pedido_id"],))
    db.ejecutar("UPDATE acciones_pendientes SET estado = 'confirmada' WHERE accion_id = ?", (accion_id,))
    return f"Devolución procesada: {pedido['nombre']} — ${pedido['precio_usd']} USD devueltos al cliente."
