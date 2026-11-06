# api.py — API HTTP del servicio de IA (equivale a una Minimal API de ASP.NET Core)
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from strands import Agent

from petshop_ai import servicios
from petshop_ai.agente import crear_agente
from petshop_ai.config import get_model, get_settings
from petshop_ai.schemas import AccionPendiente, ChatRequest, ChatResponse, Intencion, IntencionRequest
from petshop_ai.servicios import ErrorDeDominio

app = FastAPI(title="PetShop AI Service")

# Historial por conversación. En memoria: alcanza para una instancia; con varias réplicas iría a Redis.
_sesiones: dict[str, tuple[str, Agent]] = {}


def cliente_autenticado(
    x_internal_key: Annotated[str, Header()],
    x_cliente_id: Annotated[str, Header()],
) -> str:
    """Solo la API .NET (que autentica al usuario) puede llamar a este servicio y decirnos quién es."""
    if x_internal_key != get_settings().internal_api_key:
        raise HTTPException(status_code=401, detail="Clave interna inválida")
    try:
        servicios.obtener_cliente(x_cliente_id)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Cliente desconocido") from None
    return x_cliente_id


ClienteId = Annotated[str, Depends(cliente_autenticado)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, cliente_id: ClienteId) -> ChatResponse:
    session_id = req.session_id or str(uuid.uuid4())
    duenio, agente = _sesiones.get(session_id, (cliente_id, None))
    if duenio != cliente_id:
        raise HTTPException(status_code=403, detail="La sesión pertenece a otro cliente")
    if agente is None:
        agente = crear_agente()
        _sesiones[session_id] = (cliente_id, agente)

    resultado = agente(req.mensaje, invocation_state={"cliente_id": cliente_id})
    return ChatResponse(
        session_id=session_id,
        respuesta=str(resultado).strip(),
        acciones_pendientes=[AccionPendiente(**a) for a in servicios.acciones_pendientes(cliente_id)],
    )


@app.post("/acciones/{accion_id}/confirmar")
def confirmar(accion_id: int, cliente_id: ClienteId) -> dict:
    try:
        return {"resultado": servicios.confirmar_accion(cliente_id, accion_id)}
    except ErrorDeDominio as e:
        raise HTTPException(status_code=409, detail=str(e)) from None


@app.post("/intencion", response_model=Intencion)
def intencion(req: IntencionRequest) -> Intencion:
    """Salida estructurada: el modelo devuelve un objeto validado por Pydantic, no texto libre."""
    clasificador = Agent(
        model=get_model(),
        system_prompt="Clasificas mensajes de clientes de un pet shop. Responde solo con la estructura pedida.",
        callback_handler=None,
    )
    resultado = clasificador(req.mensaje, structured_output_model=Intencion)
    return resultado.structured_output
