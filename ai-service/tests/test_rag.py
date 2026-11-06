import psycopg
import pytest

from petshop_ai.config import get_settings
from petshop_ai.rag.documentos import cargar_todo, chunks_de_markdown, normalizar
from petshop_ai.rag.retriever import fusion_rrf
from petshop_ai.rag.store import Resultado, consulta_lexica


def r(cid: str) -> Resultado:
    return Resultado(chunk_id=cid, doc_id=cid, titulo="", seccion="", fuente="conocimiento", contenido="")


def test_normalizar_quita_acentos_y_mayusculas():
    assert normalizar("Alimentación ÑANDÚ") == "alimentacion nandu"


def test_consulta_lexica_usa_or_y_descarta_stopwords():
    assert consulta_lexica("¿Qué alimento para gatos castrados?") == "alimento | gatos | castrados"
    assert consulta_lexica("¿y?") is None


def test_rrf_premia_lo_que_aparece_en_ambas_listas():
    vectorial = [r("a"), r("b"), r("c")]
    lexica = [r("c"), r("d")]
    assert [x.chunk_id for x in fusion_rrf([vectorial, lexica])][:2] == ["c", "a"]


def test_chunking_por_seccion_con_metadatos():
    chunks = chunks_de_markdown(get_settings().data_dir / "knowledge" / "antiparasitarios.md")
    ids = [c.chunk_id for c in chunks]
    assert "antiparasitarios#nunca-uses-pipetas-de-perro-en-gatos" in ids
    assert all(c.especies == ["perro", "gato"] for c in chunks)
    assert all(c.contenido and "##" not in c.contenido for c in chunks)


def test_ids_de_chunks_unicos_y_catalogo_sin_precios():
    chunks = cargar_todo(get_settings().data_dir)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    productos = [c for c in chunks if c.fuente == "producto"]
    assert productos and all("USD" not in c.contenido for c in productos)


def _db_disponible() -> bool:
    try:
        with psycopg.connect(get_settings().knowledge_db_url, connect_timeout=2) as conn:
            return conn.execute("SELECT count(*) FROM chunks").fetchone()[0] > 0
    except psycopg.Error:
        return False


@pytest.mark.skipif(not _db_disponible(), reason="Requiere Postgres con el índice cargado (docker compose up + ingest)")
def test_busqueda_lexica_con_filtro_de_especie():
    from petshop_ai.rag.store import PgVectorStore

    resultados = PgVectorStore().buscar_lexica("arena aglomerante", k=5, especie="gato")
    assert resultados
    assert all(x.doc_id.startswith("producto:") or x.doc_id == "gatos-en-casa" for x in resultados)
