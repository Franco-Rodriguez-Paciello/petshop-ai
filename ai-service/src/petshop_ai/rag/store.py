# store.py — almacenamiento en Postgres + pgvector, con índice vectorial (HNSW) y léxico (full-text)
import re
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row

from petshop_ai.config import get_settings
from petshop_ai.rag.documentos import Chunk, normalizar

STOPWORDS = {
    "que", "para", "como", "con", "los", "las", "del", "una", "uno", "por", "mas", "mi", "mis", "tu",
    "sus", "hay", "puedo", "tienen", "tiene", "cual", "cuales", "cuanto", "donde", "cuando", "este", "esta",
}


@dataclass
class Resultado:
    chunk_id: str
    doc_id: str
    titulo: str
    seccion: str
    fuente: str
    contenido: str
    score: float = 0.0


def _vector_literal(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def consulta_lexica(texto: str) -> str | None:
    """'¿Qué alimento para gatos castrados?' -> 'alimento | gatos | castrados' (OR para priorizar recall)."""
    palabras = [p for p in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(p) > 2 and p not in STOPWORDS]
    return " | ".join(dict.fromkeys(palabras)) or None


class PgVectorStore:
    def __init__(self, url: str | None = None, dim: int | None = None):
        s = get_settings()
        self.url = url or s.knowledge_db_url
        self.dim = dim or s.embedding_dim

    @contextmanager
    def _conn(self):
        with psycopg.connect(self.url, row_factory=dict_row) as conn:
            yield conn

    def crear_esquema(self) -> None:
        with self._conn() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id text PRIMARY KEY,
                    doc_id text NOT NULL,
                    titulo text NOT NULL,
                    seccion text NOT NULL,
                    fuente text NOT NULL,
                    categoria text NOT NULL,
                    especies text[] NOT NULL,
                    contenido text NOT NULL,
                    texto_busqueda text NOT NULL,
                    hash text NOT NULL,
                    embedding vector({self.dim}) NOT NULL,
                    tsv tsvector GENERATED ALWAYS AS (to_tsvector('spanish', texto_busqueda)) STORED
                )""")
            conn.execute("CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops)")
            conn.execute("CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv)")

    def hashes(self) -> dict[str, str]:
        with self._conn() as conn:
            return {r["chunk_id"]: r["hash"] for r in conn.execute("SELECT chunk_id, hash FROM chunks")}

    def upsert(self, chunks: list[Chunk], vectores: list[list[float]]) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO chunks (chunk_id, doc_id, titulo, seccion, fuente, categoria, especies, contenido,
                                       texto_busqueda, hash, embedding)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                   ON CONFLICT (chunk_id) DO UPDATE SET
                     doc_id = EXCLUDED.doc_id, titulo = EXCLUDED.titulo, seccion = EXCLUDED.seccion,
                     fuente = EXCLUDED.fuente, categoria = EXCLUDED.categoria, especies = EXCLUDED.especies,
                     contenido = EXCLUDED.contenido, texto_busqueda = EXCLUDED.texto_busqueda,
                     hash = EXCLUDED.hash, embedding = EXCLUDED.embedding""",
                [
                    (c.chunk_id, c.doc_id, c.titulo, c.seccion, c.fuente, c.categoria, c.especies, c.contenido,
                     normalizar(c.texto_para_embedding), c.hash, _vector_literal(v))
                    for c, v in zip(chunks, vectores, strict=True)
                ],
            )

    def borrar_excepto(self, chunk_ids: set[str]) -> int:
        with self._conn() as conn:
            return conn.execute("DELETE FROM chunks WHERE NOT (chunk_id = ANY(%s))", (list(chunk_ids),)).rowcount

    @staticmethod
    def _filtros(especie: str | None, fuente: str | None) -> tuple[str, list]:
        sql, params = "", []
        if especie:
            sql += " AND especies && %s::text[]"
            params.append([normalizar(especie).strip(), "todas"])
        if fuente:
            sql += " AND fuente = %s"
            params.append(fuente)
        return sql, params

    def buscar_vectorial(self, vector: list[float], k: int, especie: str | None = None,
                         fuente: str | None = None) -> list[Resultado]:
        filtro, params = self._filtros(especie, fuente)
        with self._conn() as conn:
            filas = conn.execute(
                f"""SELECT chunk_id, doc_id, titulo, seccion, fuente, contenido,
                           1 - (embedding <=> %s::vector) AS score
                    FROM chunks WHERE true {filtro}
                    ORDER BY embedding <=> %s::vector LIMIT %s""",
                [_vector_literal(vector), *params, _vector_literal(vector), k],
            ).fetchall()
        return [Resultado(**f) for f in filas]

    def buscar_lexica(self, texto: str, k: int, especie: str | None = None,
                      fuente: str | None = None) -> list[Resultado]:
        tsquery = consulta_lexica(texto)
        if not tsquery:
            return []
        filtro, params = self._filtros(especie, fuente)
        with self._conn() as conn:
            filas = conn.execute(
                f"""SELECT chunk_id, doc_id, titulo, seccion, fuente, contenido,
                           ts_rank_cd(tsv, q) AS score
                    FROM chunks, to_tsquery('spanish', %s) q
                    WHERE tsv @@ q {filtro}
                    ORDER BY score DESC LIMIT %s""",
                [tsquery, *params, k],
            ).fetchall()
        return [Resultado(**f) for f in filas]
