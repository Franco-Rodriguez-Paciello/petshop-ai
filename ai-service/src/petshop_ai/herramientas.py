# herramientas.py — adaptadores finos entre el LLM y la capa de servicios.
# La identidad del cliente viaja en invocation_state (lo pone el código); el modelo no puede elegirla.
from strands import ToolContext, tool

from petshop_ai import servicios
from petshop_ai.servicios import ErrorDeDominio


def _cliente_id(tool_context: ToolContext) -> str:
    cliente_id = tool_context.invocation_state.get("cliente_id")
    if not cliente_id:
        raise PermissionError("No hay un cliente autenticado en esta conversación.")
    return cliente_id


@tool
def listar_productos() -> str:
    """Lista el catálogo completo de productos disponibles en el pet shop.

    Returns:
        Un listado con el ID, nombre, precio y stock de cada producto.
    """
    return "\n".join(
        f"{p['producto_id']}: {p['nombre']} — ${p['precio_usd']} USD — Stock: {p['stock']} unidades"
        for p in servicios.listar_productos()
    )


@tool
def consultar_producto(producto_id: str) -> str:
    """Consulta la información detallada de un producto específico por su ID.

    Args:
        producto_id: El identificador del producto, p. ej. "AL-101"
    """
    try:
        p = servicios.consultar_producto(producto_id)
    except ErrorDeDominio as e:
        validos = [p["producto_id"] for p in servicios.listar_productos()]
        return f"{e} IDs válidos: {validos}"
    return f"{p['nombre']} — ${p['precio_usd']} USD — Stock: {p['stock']} unidades"


@tool(context=True)
def mis_pedidos(tool_context: ToolContext) -> str:
    """Consulta los pedidos del cliente autenticado en esta conversación, con fechas y estado."""
    pedidos = servicios.pedidos_del_cliente(_cliente_id(tool_context))
    if not pedidos:
        return "No tienes pedidos registrados."
    return "\n".join(
        f"Pedido {p['pedido_id']}: {p['nombre']} — ${p['precio_usd']} USD — "
        f"pedido el {p['fecha_pedido']} — estado: {p['estado']}"
        for p in pedidos
    )


@tool(context=True)
def solicitar_devolucion(pedido_id: int, tool_context: ToolContext) -> str:
    """Prepara la devolución de un pedido del cliente autenticado, si cumple la política del pet shop.

    La política permite devoluciones hasta 30 días después de la fecha del pedido.
    Esta herramienta NO ejecuta la devolución: deja una solicitud pendiente que el cliente
    debe confirmar con el botón "Confirmar" de la aplicación.

    Args:
        pedido_id: El número del pedido a devolver (se obtiene con mis_pedidos)
    """
    try:
        accion = servicios.solicitar_devolucion(_cliente_id(tool_context), pedido_id)
    except ErrorDeDominio as e:
        return str(e)
    return (
        f"Solicitud de devolución #{accion['accion_id']} creada para {accion['producto']} "
        f"(${accion['monto_usd']} USD). Queda PENDIENTE hasta que el cliente la confirme en la aplicación."
    )


TODAS = [listar_productos, consultar_producto, mis_pedidos, solicitar_devolucion]
