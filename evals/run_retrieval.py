"""Evalúa SOLO la recuperación (sin LLM): hit@k, recall@k y MRR para cada modo de búsqueda.

Uso: uv run --directory ai-service python ../evals/run_retrieval.py [--k 5]
"""

import argparse
import statistics
import time

from comun import cargar_casos, coincide_fuente, guardar

from petshop_ai.rag.retriever import get_retriever

MODOS = ["lexico", "vectorial", "hibrido", "hibrido+rerank"]


def evaluar(k: int) -> dict:
    casos = [c for c in cargar_casos() if c.fuentes]
    retriever = get_retriever()
    resumen, detalle = {}, []

    for modo in MODOS:
        hits, recalls, rrs, latencias = [], [], [], []
        for caso in casos:
            t0 = time.perf_counter()
            ids = [r.chunk_id for r in retriever.buscar(caso.pregunta, k=k, modo=modo)]
            latencias.append((time.perf_counter() - t0) * 1000)

            encontradas = [e for e in caso.fuentes if any(coincide_fuente(i, e) for i in ids)]
            primer = next((pos for pos, i in enumerate(ids, 1) if any(coincide_fuente(i, e) for e in caso.fuentes)), None)
            hits.append(1.0 if encontradas else 0.0)
            # Para casos con varias fuentes alternativas (p. ej. varios SKUs válidos) basta con una
            recalls.append(len(encontradas) / len(caso.fuentes) if caso.categoria != "producto" else float(bool(encontradas)))
            rrs.append(1.0 / primer if primer else 0.0)
            detalle.append({"modo": modo, "caso": caso.id, "recuperados": ids, "hit": bool(encontradas)})

        resumen[modo] = {
            f"hit@{k}": round(statistics.mean(hits), 3),
            f"recall@{k}": round(statistics.mean(recalls), 3),
            "mrr": round(statistics.mean(rrs), 3),
            "latencia_p50_ms": round(statistics.median(latencias), 1),
        }
    return {"k": k, "casos": len(casos), "resumen": resumen, "detalle": detalle}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    resultado = evaluar(parser.parse_args().k)

    k = resultado["k"]
    print(f"\nRecuperación sobre {resultado['casos']} casos (k={k})\n")
    print(f"| Modo | hit@{k} | recall@{k} | MRR | Latencia p50 (ms) |")
    print("|---|---|---|---|---|")
    for modo, m in resultado["resumen"].items():
        print(f"| {modo} | {m[f'hit@{k}']:.3f} | {m[f'recall@{k}']:.3f} | {m['mrr']:.3f} | {m['latencia_p50_ms']} |")

    fallos = [d for d in resultado["detalle"] if d["modo"] == "hibrido+rerank" and not d["hit"]]
    if fallos:
        print("\nFallos de hibrido+rerank:", ", ".join(f["caso"] for f in fallos))
    print(f"\nGuardado en {guardar('retrieval', resultado)}")


if __name__ == "__main__":
    main()
