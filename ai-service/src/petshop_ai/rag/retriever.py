# retriever.py — búsqueda híbrida (vectorial + léxica) fusionada con RRF y reordenada con un cross-encoder
from dataclasses import replace
from functools import lru_cache
from typing import Protocol

from petshop_ai.config import get_settings
from petshop_ai.rag.embeddings import Embedder, OllamaEmbedder
from petshop_ai.rag.store import PgVectorStore, Resultado


def fusion_rrf(listas: list[list[Resultado]], k: int = 60) -> list[Resultado]:
    """Reciprocal Rank Fusion: combina rankings sin tener que calibrar scores de escalas distintas."""
    puntajes: dict[str, float] = {}
    por_id: dict[str, Resultado] = {}
    for lista in listas:
        for rank, r in enumerate(lista, start=1):
            puntajes[r.chunk_id] = puntajes.get(r.chunk_id, 0.0) + 1.0 / (k + rank)
            por_id.setdefault(r.chunk_id, r)
    orden = sorted(puntajes, key=puntajes.get, reverse=True)
    return [replace(por_id[cid], score=puntajes[cid]) for cid in orden]


class Reranker(Protocol):
    def rerank(self, consulta: str, candidatos: list[Resultado]) -> list[Resultado]: ...


class SinReranker:
    def rerank(self, consulta: str, candidatos: list[Resultado]) -> list[Resultado]:
        return candidatos


class BgeReranker:
    """Cross-encoder multilingüe (ONNX int8, corre en CPU): lee consulta y chunk juntos, más preciso que el embedding."""

    def __init__(self, model: str | None = None):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.encoder = TextCrossEncoder(model_name=model or get_settings().reranker_model)

    def rerank(self, consulta: str, candidatos: list[Resultado]) -> list[Resultado]:
        if not candidatos:
            return []
        textos = [f"{c.titulo} > {c.seccion}\n{c.contenido}" for c in candidatos]
        scores = list(self.encoder.rerank(consulta, textos))
        ordenados = sorted(zip(candidatos, scores, strict=True), key=lambda x: x[1], reverse=True)
        return [replace(c, score=float(s)) for c, s in ordenados]


class HybridRetriever:
    def __init__(self, store: PgVectorStore, embedder: Embedder, reranker: Reranker, candidatos: int = 20):
        self.store = store
        self.embedder = embedder
        self.reranker = reranker
        self.candidatos = candidatos

    def buscar(self, consulta: str, k: int = 5, especie: str | None = None, fuente: str | None = None,
               modo: str = "hibrido") -> list[Resultado]:
        """modo: 'vectorial' | 'lexico' | 'hibrido' | 'hibrido+rerank' (para comparar en las evals)."""
        vectorial = lexica = []
        if modo != "lexico":
            vector = self.embedder.embed([consulta])[0]
            vectorial = self.store.buscar_vectorial(vector, self.candidatos, especie, fuente)
        if modo != "vectorial":
            lexica = self.store.buscar_lexica(consulta, self.candidatos, especie, fuente)

        if modo == "vectorial":
            return vectorial[:k]
        if modo == "lexico":
            return lexica[:k]
        fusion = fusion_rrf([vectorial, lexica])
        if modo == "hibrido+rerank":
            fusion = self.reranker.rerank(consulta, fusion[: self.candidatos])
        return fusion[:k]


@lru_cache
def get_retriever() -> HybridRetriever:
    s = get_settings()
    reranker: Reranker = BgeReranker() if s.reranker == "bge" else SinReranker()
    return HybridRetriever(PgVectorStore(), OllamaEmbedder(), reranker)
