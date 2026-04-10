"""
Configuration management for Ship Fault Knowledge Graph.

Loads settings from .env file and provides typed access to all configuration values.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)


class Neo4jConfig:
    URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    USER = os.getenv("NEO4J_USER", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "your_neo4j_password")
    DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


class OllamaConfig:
    BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b")
    EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


class BailianConfig:
    API_KEY = os.getenv("BAILIAN_API_KEY", "")
    BASE_URL = os.getenv("BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL = os.getenv("BAILIAN_MODEL", "qwen-plus")


class KGBuilderConfig:
    CHUNK_SIZE = int(os.getenv("KG_CHUNK_SIZE", "2000"))
    CHUNK_OVERLAP = int(os.getenv("KG_CHUNK_OVERLAP", "200"))
    ON_ERROR = os.getenv("KG_ON_ERROR", "IGNORE")
    PERFORM_ENTITY_RESOLUTION = os.getenv("KG_PERFORM_ENTITY_RESOLUTION", "true").lower() == "true"
    FROM_PDF = os.getenv("KG_FROM_PDF", "false").lower() == "true"


class VectorIndexConfig:
    INDEX_NAME = os.getenv("NEO4J_VECTOR_INDEX_NAME", "ship_fault_vector_index")
    DIMENSIONS = int(os.getenv("NEO4J_VECTOR_DIMENSIONS", "768"))
    SIMILARITY_FN = os.getenv("NEO4J_VECTOR_SIMILARITY_FN", "cosine")
    FULLTEXT_INDEX_NAME = os.getenv("NEO4J_FULLTEXT_INDEX_NAME", "ship_fault_fulltext_index")


class RAGConfig:
    TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0"))


DATA_DIR = Path(__file__).parent.parent / "data"
