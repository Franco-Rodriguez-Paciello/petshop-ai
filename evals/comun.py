# comun.py — carga del golden set y chequeos deterministas compartidos por los runners
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from petshop_ai.rag.documentos import normalizar

RAIZ = Path(__file__).resolve().parent
RESULTADOS = RAIZ / "results"


@dataclass
class Caso:
    id: str
    categoria: str
    pregunta: str
    cliente: str = "C-001"
    fuentes: list[str] = field(default_factory=list)
    herramientas: list[str] = field(default_factory=list)
    sin_herramientas: list[str] = field(default_factory=list)
    args: dict[str, dict] = field(default_factory=dict)
    contiene: list[str] = field(default_factory=list)
    no_contiene: list[str] = field(default_factory=list)
    criterio: str = ""
    post: dict | None = None
    requiere: list[str] = field(default_factory=list)


def cargar_casos(ruta: Path = RAIZ / "golden_set.yaml") -> list[Caso]:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    casos = [Caso(**c) for c in datos["casos"]]
    ids = [c.id for c in casos]
    assert len(ids) == len(set(ids)), "IDs duplicados en el golden set"
    return casos


def coincide_fuente(chunk_id: str, esperada: str) -> bool:
    """'antiparasitarios' matchea cualquier sección del doc; 'doc#seccion' y 'producto:SKU' matchean exacto."""
    return chunk_id == esperada or chunk_id.startswith(esperada + "#")


def contiene_alternativas(texto: str, patron: str) -> bool:
    t = normalizar(texto)
    return any(normalizar(alt) in t for alt in patron.split("|"))


def guardar(nombre: str, datos: dict) -> Path:
    RESULTADOS.mkdir(exist_ok=True)
    ruta = RESULTADOS / f"{nombre}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta
