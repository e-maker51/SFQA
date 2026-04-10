"""
LLM Factory

Creates LLM and Embedder instances for the Knowledge Graph pipeline.

- OllamaLLM: Local model for entity/relation extraction during KG building
- OpenAILLM (Bailian): Cloud Qwen-Plus model for RAG queries
- OllamaEmbeddings: Local embedding model for vector operations
"""
import logging

from neo4j_graphrag.llm import OllamaLLM, OpenAILLM
from neo4j_graphrag.embeddings import OllamaEmbeddings

from ..config import OllamaConfig, BailianConfig

logger = logging.getLogger(__name__)


def create_ollama_llm(
    model_name: str = None,
    base_url: str = None,
    model_params: dict = None,
) -> OllamaLLM:
    """
    Create an OllamaLLM instance for local model inference.

    Used primarily for entity and relation extraction during KG building.
    """
    model = model_name or OllamaConfig.LLM_MODEL
    url = base_url or OllamaConfig.BASE_URL
    params = model_params or {"temperature": 0}

    logger.info(f"Creating OllamaLLM: model={model}, base_url={url}")

    return OllamaLLM(
        model_name=model,
        model_params=params,
        base_url=url,
    )


def create_bailian_llm(
    model_name: str = None,
    api_key: str = None,
    base_url: str = None,
    model_params: dict = None,
) -> OpenAILLM:
    """
    Create an OpenAILLM instance configured for Alibaba Bailian (DashScope).

    Bailian provides an OpenAI-compatible API endpoint, so we reuse OpenAILLM
    with the Bailian base URL and API key.

    Used for RAG query generation and Text2Cypher tasks.
    """
    model = model_name or BailianConfig.MODEL
    key = api_key or BailianConfig.API_KEY
    url = base_url or BailianConfig.BASE_URL
    params = model_params or {"temperature": 0}

    if not key:
        raise ValueError(
            "Bailian API key is required. Set BAILIAN_API_KEY in .env "
            "or pass api_key parameter."
        )

    logger.info(f"Creating BailianLLM (OpenAI-compatible): model={model}, base_url={url}")

    return OpenAILLM(
        model_name=model,
        model_params=params,
        api_key=key,
        base_url=url,
    )


def create_embedder(
    model_name: str = None,
    base_url: str = None,
) -> OllamaEmbeddings:
    """
    Create an OllamaEmbeddings instance for generating vector embeddings.

    Uses nomic-embed-text by default, which produces 768-dimensional vectors.
    """
    model = model_name or OllamaConfig.EMBEDDING_MODEL
    url = base_url or OllamaConfig.BASE_URL

    logger.info(f"Creating OllamaEmbeddings: model={model}, base_url={url}")

    return OllamaEmbeddings(
        model=model,
        base_url=url,
    )
