# documentos.py — carga y chunking de la base de conocimiento y del catálogo
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    titulo: str
    seccion: str
    fuente: str  # "conocimiento" | "producto"
    categoria: str
    especies: list[str] = field(default_factory=list)
    contenido: str = ""

    @property
    def texto_para_embedding(self) -> str:
        # Chunk "contextualizado": el título y la sección viajan con el texto para que el embedding no pierda el tema
        return f"{self.titulo} > {self.seccion}\n{self.contenido}"

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.texto_para_embedding.encode()).hexdigest()[:16]


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos: 'Alimentación' y 'alimentacion' deben matchear en la búsqueda léxica."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_acentos.lower()


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")


def _front_matter(texto: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.DOTALL)
    if not m:
        raise ValueError("El documento no tiene front matter")
    meta = dict(linea.split(":", 1) for linea in m.group(1).splitlines() if ":" in linea)
    return {k.strip(): v.strip() for k, v in meta.items()}, texto[m.end():]


def chunks_de_markdown(ruta: Path) -> list[Chunk]:
    """Un chunk por sección '## ': las secciones de estas guías son cortas y autocontenidas."""
    meta, cuerpo = _front_matter(ruta.read_text(encoding="utf-8").replace("\r\n", "\n"))
    especies = [e.strip() for e in meta.get("especies", "todas").split(",")]
    chunks = []
    for bloque in re.split(r"^## ", cuerpo, flags=re.MULTILINE):
        if not bloque.strip():
            continue
        seccion, _, contenido = bloque.partition("\n")
        chunks.append(Chunk(
            chunk_id=f"{meta['id']}#{slug(seccion)}",
            doc_id=meta["id"],
            titulo=meta["titulo"],
            seccion=seccion.strip(),
            fuente="conocimiento",
            categoria=meta.get("categoria", ""),
            especies=especies,
            contenido=contenido.strip(),
        ))
    return chunks


def chunks_de_catalogo(ruta: Path) -> list[Chunk]:
    """Un chunk por producto, sin precio ni stock: esos datos cambian y se consultan en vivo con herramientas."""
    productos = json.loads(ruta.read_text(encoding="utf-8"))
    return [
        Chunk(
            chunk_id=f"producto:{p['sku']}",
            doc_id=f"producto:{p['sku']}",
            titulo=p["name"],
            seccion=f"{p['category']} para {p['species']}",
            fuente="producto",
            categoria=p["category"],
            especies=[p["species"]],
            contenido=(f"{p['description']} Marca {p['brand']}. SKU {p['sku']}. "
                       f"Etapa: {p['lifeStage']}. Tamaño: {p['size']}."),
        )
        for p in productos
    ]


def cargar_todo(data_dir: Path) -> list[Chunk]:
    chunks = [c for ruta in sorted((data_dir / "knowledge").glob("*.md")) for c in chunks_de_markdown(ruta)]
    return chunks + chunks_de_catalogo(data_dir / "catalog" / "products.json")
