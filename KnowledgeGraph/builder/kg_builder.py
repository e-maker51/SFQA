"""
Ship Fault Knowledge Graph Builder

Implements the KG construction pipeline using neo4j-graphrag's SimpleKGPipeline.
Supports building knowledge graphs from text files and raw text strings.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

from neo4j import GraphDatabase
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)

from ..config import Neo4jConfig, KGBuilderConfig, DATA_DIR
from ..schema import get_ship_fault_schema_dict
from ..llm import create_ollama_llm, create_embedder

logger = logging.getLogger(__name__)


class ShipFaultKGBBuilder:
    """
    Builds a ship fault knowledge graph from unstructured text data.

    Uses SimpleKGPipeline from neo4j-graphrag with a domain-specific schema
    for ship electrical equipment faults, symptoms, causes, and solutions.
    """

    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None,
        neo4j_database: str = None,
        llm_model: str = None,
        embedding_model: str = None,
        ollama_base_url: str = None,
    ):
        self._neo4j_uri = neo4j_uri or Neo4jConfig.URI
        self._neo4j_user = neo4j_user or Neo4jConfig.USER
        self._neo4j_password = neo4j_password or Neo4jConfig.PASSWORD
        self._neo4j_database = neo4j_database or Neo4jConfig.DATABASE

        self._driver = GraphDatabase.driver(
            self._neo4j_uri,
            auth=(self._neo4j_user, self._neo4j_password),
        )

        self._llm = create_ollama_llm(
            model_name=llm_model,
            base_url=ollama_base_url,
        )

        self._embedder = create_embedder(
            model_name=embedding_model,
            base_url=ollama_base_url,
        )

        self._schema = get_ship_fault_schema_dict()

        self._text_splitter = FixedSizeSplitter(
            chunk_size=KGBuilderConfig.CHUNK_SIZE,
            chunk_overlap=KGBuilderConfig.CHUNK_OVERLAP,
        )

        self._pipeline = SimpleKGPipeline(
            llm=self._llm,
            driver=self._driver,
            embedder=self._embedder,
            schema=self._schema,
            from_pdf=KGBuilderConfig.FROM_PDF,
            text_splitter=self._text_splitter,
            on_error=KGBuilderConfig.ON_ERROR,
            perform_entity_resolution=KGBuilderConfig.PERFORM_ENTITY_RESOLUTION,
            neo4j_database=self._neo4j_database,
        )

        logger.info("ShipFaultKGBBuilder initialized successfully")

    async def build_from_text(
        self,
        text: str,
        document_metadata: Optional[dict] = None,
    ):
        """
        Build knowledge graph from raw text content.

        Args:
            text: The text content to process.
            document_metadata: Optional metadata to attach to the document node.
        """
        logger.info(f"Building KG from text (length={len(text)})")
        result = await self._pipeline.run_async(
            text=text,
            document_metadata=document_metadata,
        )
        logger.info(f"KG build complete: {result}")
        return result

    async def build_from_file(
        self,
        file_path: str,
        document_metadata: Optional[dict] = None,
    ):
        """
        Build knowledge graph from a text file.

        Args:
            file_path: Path to the text file.
            document_metadata: Optional metadata to attach to the document node.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Building KG from file: {file_path}")

        text = path.read_text(encoding="utf-8")
        metadata = document_metadata or {}
        metadata.setdefault("source", str(path))
        metadata.setdefault("filename", path.name)

        return await self.build_from_text(text, metadata)

    async def build_from_data_dir(
        self,
        data_dir: str = None,
        file_pattern: str = "*.md",
    ):
        """
        Build knowledge graph from all matching files in the data directory.

        Args:
            data_dir: Directory containing source files. Defaults to project data dir.
            file_pattern: Glob pattern for file selection.
        """
        directory = Path(data_dir) if data_dir else DATA_DIR
        if not directory.exists():
            raise FileNotFoundError(f"Data directory not found: {directory}")

        files = sorted(directory.glob(file_pattern))
        if not files:
            logger.warning(f"No files matching '{file_pattern}' in {directory}")
            return []

        logger.info(f"Found {len(files)} files to process in {directory}")

        results = []
        for file_path in files:
            try:
                result = await self.build_from_file(str(file_path))
                results.append({"file": str(file_path), "result": result})
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results.append({"file": str(file_path), "error": str(e)})

        return results

    def build_from_text_sync(self, text: str, document_metadata: Optional[dict] = None):
        """Synchronous wrapper for build_from_text."""
        return asyncio.run(self.build_from_text(text, document_metadata))

    def build_from_file_sync(self, file_path: str, document_metadata: Optional[dict] = None):
        """Synchronous wrapper for build_from_file."""
        return asyncio.run(self.build_from_file(file_path, document_metadata))

    def build_from_data_dir_sync(self, data_dir: str = None, file_pattern: str = "*.md"):
        """Synchronous wrapper for build_from_data_dir."""
        return asyncio.run(self.build_from_data_dir(data_dir, file_pattern))

    def close(self):
        """Close the Neo4j driver connection."""
        self._driver.close()
        logger.info("Neo4j driver closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
