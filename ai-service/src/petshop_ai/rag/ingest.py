# ingest.py — indexa la base de conocimiento y el catálogo. Idempotente: solo re-embebe lo que cambió.
# Uso: uv run python -m petshop_ai.rag.ingest
import time

from petshop_ai.config import get_settings
from petshop_ai.rag.documentos import cargar_todo
from petshop_ai.rag.embeddings import OllamaEmbedder
from petshop_ai.rag.store import PgVectorStore


def ingestar() -> dict:
    inicio = time.perf_counter()
    store = PgVectorStore()
    store.crear_esquema()

    chunks = cargar_todo(get_settings().data_dir)
    existentes = store.hashes()
    cambiados = [c for c in chunks if existentes.get(c.chunk_id) != c.hash]
    if cambiados:
        vectores = OllamaEmbedder().embed([c.texto_para_embedding for c in cambiados])
        store.upsert(cambiados, vectores)
    borrados = store.borrar_excepto({c.chunk_id for c in chunks})

    return {
        "chunks": len(chunks),
        "embebidos": len(cambiados),
        "borrados": borrados,
        "segundos": round(time.perf_counter() - inicio, 1),
    }


if __name__ == "__main__":
    print(ingestar())
