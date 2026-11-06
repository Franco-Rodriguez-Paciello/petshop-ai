from datetime import date, timedelta

import pytest

from petshop_ai import db, servicios
from petshop_ai.servicios import ErrorDeDominio

MARIA, CARLOS = "C-001", "C-002"


def test_listar_productos_devuelve_catalogo_ordenado():
    ids = [p["producto_id"] for p in servicios.listar_productos()]
    assert ids == ["AC-301", "AL-101", "JU-201", "SN-401"]


def test_consultar_producto_normaliza_id():
    assert servicios.consultar_producto(" al-101 ")["nombre"].startswith("Alimento Premium")


def test_consultar_producto_inexistente():
    with pytest.raises(ErrorDeDominio):
        servicios.consultar_producto("XX-999")


def test_pedidos_solo_del_cliente():
    pedidos = servicios.pedidos_del_cliente(MARIA)
    assert {p["pedido_id"] for p in pedidos} == {1, 2}


def test_solicitar_devolucion_elegible_crea_accion_pendiente_sin_ejecutar():
    accion = servicios.solicitar_devolucion(MARIA, 1)
    assert accion["tipo"] == "devolucion"
    assert db.obtener_uno("SELECT estado FROM pedidos WHERE pedido_id = 1")["estado"] == "completado"
    assert len(servicios.acciones_pendientes(MARIA)) == 1


def test_solicitar_devolucion_es_idempotente():
    a1 = servicios.solicitar_devolucion(MARIA, 1)
    a2 = servicios.solicitar_devolucion(MARIA, 1)
    assert a1["accion_id"] == a2["accion_id"]


def test_devolucion_fuera_de_ventana():
    with pytest.raises(ErrorDeDominio, match="venció"):
        servicios.solicitar_devolucion(MARIA, 2)


def test_devolucion_ya_devuelta():
    with pytest.raises(ErrorDeDominio, match="ya fue devuelto"):
        servicios.solicitar_devolucion(CARLOS, 3)


def test_no_se_puede_devolver_un_pedido_ajeno():
    """El bug original (IDOR): María pedía devolver el pedido 4, que es de Carlos."""
    with pytest.raises(ErrorDeDominio, match="No encontré el pedido 4"):
        servicios.solicitar_devolucion(MARIA, 4)
    assert db.obtener_uno("SELECT estado FROM pedidos WHERE pedido_id = 4")["estado"] == "completado"


def test_pedido_ajeno_e_inexistente_dan_el_mismo_mensaje():
    with pytest.raises(ErrorDeDominio) as ajeno:
        servicios.solicitar_devolucion(MARIA, 4)
    with pytest.raises(ErrorDeDominio) as inexistente:
        servicios.solicitar_devolucion(MARIA, 999)
    assert str(ajeno.value).replace("4", "N") == str(inexistente.value).replace("999", "N")


def test_pedido_id_invalido_es_error_de_contrato():
    with pytest.raises(ValueError):
        servicios.solicitar_devolucion(MARIA, 0)


def test_confirmar_ejecuta_la_devolucion():
    accion = servicios.solicitar_devolucion(MARIA, 1)
    assert "Devolución procesada" in servicios.confirmar_accion(MARIA, accion["accion_id"])
    assert db.obtener_uno("SELECT estado FROM pedidos WHERE pedido_id = 1")["estado"] == "devuelto"
    assert servicios.acciones_pendientes(MARIA) == []


def test_otro_cliente_no_puede_confirmar_mi_accion():
    accion = servicios.solicitar_devolucion(MARIA, 1)
    with pytest.raises(ErrorDeDominio):
        servicios.confirmar_accion(CARLOS, accion["accion_id"])


def test_verificar_elegibilidad_en_el_limite_exacto():
    pedido = {"pedido_id": 1, "estado": "completado", "fecha_pedido": "2026-01-01"}
    servicios.verificar_elegibilidad(pedido, hoy=date(2026, 1, 1) + timedelta(days=30))
    with pytest.raises(ErrorDeDominio):
        servicios.verificar_elegibilidad(pedido, hoy=date(2026, 1, 1) + timedelta(days=31))
