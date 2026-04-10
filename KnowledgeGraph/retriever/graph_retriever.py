"""
Ship Fault Graph Retriever

Provides multiple retrieval strategies over the ship fault knowledge graph:
- Vector search: Semantic similarity search using embeddings
- Hybrid search: Combined vector + fulltext search
- Text2Cypher: Natural language to Cypher query translation
- GraphRAG: Full RAG pipeline with LLM answer generation
"""
import logging
from typing import Optional, List

from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.generation.prompts import RagTemplate, PromptTemplate
from neo4j_graphrag.indexes import create_vector_index, create_fulltext_index
from neo4j_graphrag.schema import get_schema

from ..config import (
    Neo4jConfig,
    VectorIndexConfig,
    RAGConfig,
    BailianConfig,
)
from ..llm import create_bailian_llm, create_ollama_llm, create_embedder

logger = logging.getLogger(__name__)

SHIP_FAULT_RAG_TEMPLATE = RagTemplate(
    template="""你是一个船舶电气设备故障诊断专家。请根据以下知识图谱检索到的上下文信息，回答用户关于船舶故障的问题。
如果上下文中没有相关信息，请明确说明。回答应当专业、准确、有条理。

上下文：
{context}

示例：
{examples}

问题：
{query_text}

回答：""",
    expected_inputs=["context", "query_text", "examples"],
    system_instructions="你是一个船舶电气设备故障诊断专家，专注于利用知识图谱中的信息来回答船舶故障相关问题。",
)

SHIP_FAULT_TEXT2CYPHER_TEMPLATE = PromptTemplate(
    template="""任务：根据用户输入生成一个用于查询Neo4j图数据库的Cypher语句。

图数据库包含船舶电气设备故障相关的节点和关系：
- 节点标签：Equipment, Fault, Symptom, Cause, Solution, System, Component, DiagnosticMethod, TestMethod, SafetyMeasure
- 关系类型：HAS_FAULT, HAS_SYMPTOM, CAUSED_BY, SOLVED_BY, BELONGS_TO_SYSTEM, CONTAINS_COMPONENT, DIAGNOSED_BY, TESTED_BY, REQUIRES_SAFETY, LEADS_TO, RELATED_FAULT

Schema：
{schema}

示例（可选）：
{examples}

输入：
{query_text}

不要使用Schema中未包含的属性或关系。
响应中只包含生成的Cypher语句，不要包含三重反引号```或任何额外文本。

Cypher查询：""",
    expected_inputs=["query_text"],
)


class ShipFaultGraphRetriever:
    """
    Retrieves information from the ship fault knowledge graph using
    multiple strategies provided by neo4j-graphrag.
    """

    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None,
        neo4j_database: str = None,
    ):
        self._neo4j_uri = neo4j_uri or Neo4jConfig.URI
        self._neo4j_user = neo4j_user or Neo4jConfig.USER
        self._neo4j_password = neo4j_password or Neo4jConfig.PASSWORD
        self._neo4j_database = neo4j_database or Neo4jConfig.DATABASE

        self._driver = GraphDatabase.driver(
            self._neo4j_uri,
            auth=(self._neo4j_user, self._neo4j_password),
        )

        self._embedder = create_embedder()

        self._bailian_llm = None
        self._ollama_llm = None
        self._vector_retriever = None
        self._hybrid_retriever = None
        self._text2cypher_retriever = None
        self._graph_rag = None

        logger.info("ShipFaultGraphRetriever initialized")

    def _get_bailian_llm(self):
        if self._bailian_llm is None:
            self._bailian_llm = create_bailian_llm()
        return self._bailian_llm

    def _get_ollama_llm(self):
        if self._ollama_llm is None:
            self._ollama_llm = create_ollama_llm()
        return self._ollama_llm

    def ensure_indexes(self):
        """Create vector and fulltext indexes if they don't exist."""
        try:
            create_vector_index(
                self._driver,
                VectorIndexConfig.INDEX_NAME,
                label="Chunk",
                embedding_property="embedding",
                dimensions=VectorIndexConfig.DIMENSIONS,
                similarity_fn=VectorIndexConfig.SIMILARITY_FN,
                fail_if_exists=False,
                neo4j_database=self._neo4j_database,
            )
            logger.info(f"Vector index '{VectorIndexConfig.INDEX_NAME}' ensured")
        except Exception as e:
            logger.warning(f"Vector index creation note: {e}")

        try:
            create_fulltext_index(
                self._driver,
                VectorIndexConfig.FULLTEXT_INDEX_NAME,
                label="Chunk",
                node_properties=["text"],
                fail_if_exists=False,
                neo4j_database=self._neo4j_database,
            )
            logger.info(f"Fulltext index '{VectorIndexConfig.FULLTEXT_INDEX_NAME}' ensured")
        except Exception as e:
            logger.warning(f"Fulltext index creation note: {e}")

    def vector_search(self, query_text: str, top_k: int = None):
        """
        Perform vector similarity search over the knowledge graph.

        Args:
            query_text: Natural language query.
            top_k: Number of results to return.
        """
        k = top_k or RAGConfig.TOP_K

        if self._vector_retriever is None:
            self._vector_retriever = VectorRetriever(
                driver=self._driver,
                index_name=VectorIndexConfig.INDEX_NAME,
                embedder=self._embedder,
                neo4j_database=self._neo4j_database,
            )

        result = self._vector_retriever.search(
            query_text=query_text,
            top_k=k,
        )
        return result

    def hybrid_search(self, query_text: str, top_k: int = None):
        """
        Perform hybrid search combining vector similarity and fulltext search.

        Args:
            query_text: Natural language query.
            top_k: Number of results to return.
        """
        k = top_k or RAGConfig.TOP_K

        if self._hybrid_retriever is None:
            self._hybrid_retriever = HybridRetriever(
                driver=self._driver,
                vector_index_name=VectorIndexConfig.INDEX_NAME,
                fulltext_index_name=VectorIndexConfig.FULLTEXT_INDEX_NAME,
                embedder=self._embedder,
                neo4j_database=self._neo4j_database,
            )

        result = self._hybrid_retriever.search(
            query_text=query_text,
            top_k=k,
        )
        return result

    def text2cypher_search(self, query_text: str):
        """
        Convert natural language to Cypher and execute against the graph.

        Args:
            query_text: Natural language query.
        """
        if self._text2cypher_retriever is None:
            neo4j_schema = get_schema(
                self._driver,
                database=self._neo4j_database,
            )
            self._text2cypher_retriever = Text2CypherRetriever(
                driver=self._driver,
                llm=self._get_bailian_llm(),
                neo4j_schema=neo4j_schema,
                custom_prompt=SHIP_FAULT_TEXT2CYPHER_TEMPLATE.template,
                neo4j_database=self._neo4j_database,
            )

        result = self._text2cypher_retriever.search(query_text=query_text)
        return result

    def rag_query(
        self,
        query_text: str,
        top_k: int = None,
        retriever_type: str = "vector",
    ):
        """
        Perform full RAG query: retrieve context + generate answer.

        Args:
            query_text: Natural language question about ship faults.
            top_k: Number of context chunks to retrieve.
            retriever_type: One of 'vector', 'hybrid', 'text2cypher'.
        """
        k = top_k or RAGConfig.TOP_K

        if retriever_type == "hybrid":
            retriever = HybridRetriever(
                driver=self._driver,
                vector_index_name=VectorIndexConfig.INDEX_NAME,
                fulltext_index_name=VectorIndexConfig.FULLTEXT_INDEX_NAME,
                embedder=self._embedder,
                neo4j_database=self._neo4j_database,
            )
        elif retriever_type == "text2cypher":
            neo4j_schema = get_schema(
                self._driver,
                database=self._neo4j_database,
            )
            retriever = Text2CypherRetriever(
                driver=self._driver,
                llm=self._get_bailian_llm(),
                neo4j_schema=neo4j_schema,
                neo4j_database=self._neo4j_database,
            )
        else:
            retriever = VectorRetriever(
                driver=self._driver,
                index_name=VectorIndexConfig.INDEX_NAME,
                embedder=self._embedder,
                neo4j_database=self._neo4j_database,
            )

        rag = GraphRAG(
            retriever=retriever,
            llm=self._get_bailian_llm(),
            prompt_template=SHIP_FAULT_RAG_TEMPLATE,
        )

        result = rag.search(
            query_text=query_text,
            retriever_config={"top_k": k},
            return_context=True,
        )
        return result

    def get_graph_schema(self) -> str:
        """Get the current Neo4j graph schema as a string."""
        return get_schema(
            self._driver,
            database=self._neo4j_database,
        )

    def close(self):
        """Close the Neo4j driver connection."""
        self._driver.close()
        logger.info("Neo4j driver closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
