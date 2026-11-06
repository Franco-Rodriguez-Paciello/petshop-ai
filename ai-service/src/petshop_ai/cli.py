# cli.py — chat por consola para probar el agente sin levantar la API
import sys

from petshop_ai.agente import crear_agente


def main() -> None:
    cliente_id = sys.argv[1] if len(sys.argv) > 1 else "C-001"
    agente = crear_agente()
    print(f"Chat como cliente {cliente_id}. Escribe 'salir' para terminar.")
    while (mensaje := input("\n> ").strip()) not in ("salir", "exit"):
        if mensaje:
            print(agente(mensaje, invocation_state={"cliente_id": cliente_id}))


if __name__ == "__main__":
    main()
