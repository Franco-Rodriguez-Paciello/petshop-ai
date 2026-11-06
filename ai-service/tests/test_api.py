import pytest
from fastapi.testclient import TestClient

from petshop_ai import api, servicios

HEADERS_MARIA = {"X-Internal-Key": "dev-internal-key", "X-Cliente-Id": "C-001"}
HEADERS_CARLOS = {"X-Internal-Key": "dev-internal-key", "X-Cliente-Id": "C-002"}


class AgenteFalso:
    """Reemplaza al LLM: simula que el modelo pidió la devolución del pedido 1."""

    def __call__(self, mensaje, invocation_state):
        servicios.solicitar_devolucion(invocation_state["cliente_id"], 1)
        return "Listo, confírmala en la app."


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "crear_agente", AgenteFalso)
    api._sesiones.clear()
    return TestClient(api.app)


def test_chat_requiere_clave_interna(client):
    r = client.post("/chat", json={"mensaje": "hola"}, headers={**HEADERS_MARIA, "X-Internal-Key": "x"})
    assert r.status_code == 401


def test_chat_rechaza_cliente_desconocido(client):
    r = client.post("/chat", json={"mensaje": "hola"}, headers={**HEADERS_MARIA, "X-Cliente-Id": "C-999"})
    assert r.status_code == 401


def test_chat_devuelve_acciones_pendientes(client):
    r = client.post("/chat", json={"mensaje": "quiero devolver"}, headers=HEADERS_MARIA)
    assert r.status_code == 200
    body = r.json()
    assert body["acciones_pendientes"][0]["pedido_id"] == 1


def test_sesion_de_otro_cliente_da_403(client):
    sid = client.post("/chat", json={"mensaje": "hola"}, headers=HEADERS_MARIA).json()["session_id"]
    r = client.post("/chat", json={"mensaje": "hola", "session_id": sid}, headers=HEADERS_CARLOS)
    assert r.status_code == 403


def test_confirmar_accion_flujo_completo(client):
    accion_id = client.post("/chat", json={"mensaje": "x"}, headers=HEADERS_MARIA).json()[
        "acciones_pendientes"
    ][0]["accion_id"]
    assert client.post(f"/acciones/{accion_id}/confirmar", headers=HEADERS_CARLOS).status_code == 409
    r = client.post(f"/acciones/{accion_id}/confirmar", headers=HEADERS_MARIA)
    assert r.status_code == 200 and "Devolución procesada" in r.json()["resultado"]
