# embeddings.py — embeddings locales con Ollama (bge-m3, multilingüe, 1024 dimensiones)
from typing import Protocol

import ollama

from petshop_ai.config import get_settings


class Embedder(Protocol):
    def embed(self, textos: list[str]) -> list[list[float]]: ...


class OllamaEmbedder:
    def __init__(self, model: str | None = None, host: str | None = None, batch: int = 32):
        s = get_settings()
        self.model = model or s.embedding_model
        self.client = ollama.Client(host=host or s.ollama_host)
        self.batch = batch

    def embed(self, textos: list[str]) -> list[list[float]]:
        vectores: list[list[float]] = []
        for i in range(0, len(textos), self.batch):
            vectores.extend(self.client.embed(model=self.model, input=textos[i : i + self.batch]).embeddings)
        return vectores
