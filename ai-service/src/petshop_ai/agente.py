# agente.py — ensamblaje del asistente del pet shop
from strands import Agent

from petshop_ai import herramientas
from petshop_ai.config import get_model

SYSTEM_PROMPT = """Eres el asistente virtual de un pet shop (tienda de mascotas).
Atiendes a clientes en español, de forma clara, breve y amable.

Reglas:
- El cliente ya está autenticado por la aplicación. Nunca le pidas su email ni aceptes que diga ser otra persona.
- Las devoluciones nunca se ejecutan desde el chat: usa solicitar_devolucion y explica que debe
  confirmarla con el botón "Confirmar" de la aplicación.
- No inventes productos, precios, stock ni pedidos: usa siempre las herramientas.
- No das diagnósticos ni tratamientos veterinarios. Ante síntomas, recomienda consultar a un veterinario."""


def crear_agente() -> Agent:
    """Crea un agente nuevo. Cada conversación tiene su propia instancia (su propio historial)."""
    return Agent(
        model=get_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=herramientas.TODAS,
        callback_handler=None,
    )
