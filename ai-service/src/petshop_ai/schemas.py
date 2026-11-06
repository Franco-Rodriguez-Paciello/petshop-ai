# schemas.py — contratos de entrada/salida (equivalen a tus DTOs con DataAnnotations)
from enum import StrEnum

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class AccionPendiente(BaseModel):
    accion_id: int
    tipo: str
    pedido_id: int
    producto: str
    monto_usd: float


class ChatResponse(BaseModel):
    session_id: str
    respuesta: str
    acciones_pendientes: list[AccionPendiente] = []


class IntencionRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000)


class TipoIntencion(StrEnum):
    consulta_producto = "consulta_producto"
    cuidado_mascota = "cuidado_mascota"
    pedido = "pedido"
    devolucion = "devolucion"
    turno = "turno"
    salud_urgente = "salud_urgente"
    reclamo = "reclamo"
    fuera_de_alcance = "fuera_de_alcance"


class Intencion(BaseModel):
    """Clasificación de un mensaje de un cliente del pet shop."""

    intencion: TipoIntencion = Field(description="La intención principal del mensaje")
    especie: str | None = Field(default=None, description="Especie de mascota mencionada, p. ej. perro, gato")
    requiere_humano: bool = Field(
        description="True si debe atenderlo una persona: reclamos, emergencias de salud o enojo del cliente"
    )
    resumen: str = Field(description="Resumen de una línea del pedido del cliente")
