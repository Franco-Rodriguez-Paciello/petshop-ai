-- Cada servicio es dueño de su base: la API .NET de "petshop", el servicio de IA de "knowledge" (RAG).
CREATE DATABASE knowledge OWNER petshop;
\connect knowledge
CREATE EXTENSION IF NOT EXISTS vector;
