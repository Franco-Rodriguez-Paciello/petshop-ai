from types import SimpleNamespace

import pytest

from petshop_ai import herramientas


def ctx(cliente_id: str | None):
    return SimpleNamespace(invocation_state={"cliente_id": cliente_id} if cliente_id else {})


def test_listar_productos():
    assert "AL-101: Alimento Premium" in herramientas.listar_productos()


def test_consultar_producto_inexistente_sugiere_ids_validos():
    texto = herramientas.consultar_producto("XX-1")
    assert "No existe" in texto and "AL-101" in texto


def test_mis_pedidos_usa_el_cliente_del_contexto():
    texto = herramientas.mis_pedidos(tool_context=ctx("C-002"))
    assert "Pedido 3" in texto and "Pedido 1" not in texto


def test_herramientas_sin_cliente_autenticado_fallan():
    with pytest.raises(PermissionError):
        herramientas.mis_pedidos(tool_context=ctx(None))


def test_solicitar_devolucion_no_expone_al_modelo_el_parametro_cliente():
    """El modelo solo ve pedido_id: no puede elegir de quién es el pedido."""
    props = herramientas.solicitar_devolucion.tool_spec["inputSchema"]["json"]["properties"]
    assert set(props) == {"pedido_id"}


def test_solicitar_devolucion_ajena_devuelve_mensaje_de_dominio():
    texto = herramientas.solicitar_devolucion(pedido_id=4, tool_context=ctx("C-001"))
    assert "No encontré el pedido 4" in texto


def test_solicitar_devolucion_queda_pendiente():
    texto = herramientas.solicitar_devolucion(pedido_id=1, tool_context=ctx("C-001"))
    assert "PENDIENTE" in texto
