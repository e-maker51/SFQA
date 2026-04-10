"""
Ship Fault Knowledge Graph - Main Entry Point

Provides CLI commands for building and querying the ship fault knowledge graph.

Usage:
    python -m KnowledgeGraph.main build                    # Build KG from all data files
    python -m KnowledgeGraph.main build --file path/to/file  # Build KG from a single file
    python -m KnowledgeGraph.main build --text "some text"   # Build KG from raw text
    python -m KnowledgeGraph.main query "发电机过热怎么办"     # RAG query
    python -m KnowledgeGraph.main search "电动机故障"         # Vector search
    python -m KnowledgeGraph.main hybrid "配电板跳闸"        # Hybrid search
    python -m KnowledgeGraph.main cypher "有哪些故障由绝缘引起" # Text2Cypher
    python -m KnowledgeGraph.main stats                     # Show graph statistics
    python -m KnowledgeGraph.main test                      # Test Neo4j connection
    python -m KnowledgeGraph.main clear                     # Clear the database
"""
import argparse
import asyncio
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_build(args):
    """Build knowledge graph from data sources."""
    from .builder import ShipFaultKGBBuilder

    with ShipFaultKGBBuilder() as builder:
        if args.text:
            logger.info("Building KG from provided text")
            result = builder.build_from_text_sync(
                args.text,
                document_metadata={"source": "cli_text_input"},
            )
            print(json.dumps({"status": "success", "result": str(result)}, ensure_ascii=False, indent=2))

        elif args.file:
            logger.info(f"Building KG from file: {args.file}")
            result = builder.build_from_file_sync(args.file)
            print(json.dumps({"status": "success", "result": str(result)}, ensure_ascii=False, indent=2))

        else:
            logger.info("Building KG from data directory")
            results = builder.build_from_data_dir_sync(
                data_dir=args.data_dir,
                file_pattern=args.pattern,
            )
            print(json.dumps({"status": "success", "results": str(results)}, ensure_ascii=False, indent=2))


def cmd_query(args):
    """Perform a RAG query against the knowledge graph."""
    from .retriever import ShipFaultGraphRetriever

    with ShipFaultGraphRetriever() as retriever:
        retriever.ensure_indexes()
        result = retriever.rag_query(
            query_text=args.question,
            top_k=args.top_k,
            retriever_type=args.retriever,
        )
        print(f"\n{'='*60}")
        print(f"问题: {args.question}")
        print(f"{'='*60}")
        print(f"\n回答:\n{result.answer}")
        if hasattr(result, "context") and result.context:
            print(f"\n--- 检索上下文 ---")
            for item in result.context:
                print(f"  - {item}")


def cmd_search(args):
    """Perform vector similarity search."""
    from .retriever import ShipFaultGraphRetriever

    with ShipFaultGraphRetriever() as retriever:
        retriever.ensure_indexes()
        result = retriever.vector_search(
            query_text=args.query,
            top_k=args.top_k,
        )
        print(f"\n向量搜索结果 (query='{args.query}'):")
        for item in result.items:
            print(f"  - score={item.score:.4f} | {item.content[:200]}")


def cmd_hybrid(args):
    """Perform hybrid search."""
    from .retriever import ShipFaultGraphRetriever

    with ShipFaultGraphRetriever() as retriever:
        retriever.ensure_indexes()
        result = retriever.hybrid_search(
            query_text=args.query,
            top_k=args.top_k,
        )
        print(f"\n混合搜索结果 (query='{args.query}'):")
        for item in result.items:
            print(f"  - score={item.score:.4f} | {item.content[:200]}")


def cmd_cypher(args):
    """Perform Text2Cypher search."""
    from .retriever import ShipFaultGraphRetriever

    with ShipFaultGraphRetriever() as retriever:
        result = retriever.text2cypher_search(query_text=args.question)
        print(f"\nText2Cypher搜索结果 (query='{args.question}'):")
        for item in result.items:
            print(f"  - {item.content[:300]}")


def cmd_stats(_args):
    """Show knowledge graph statistics."""
    from .utils import get_neo4j_stats

    stats = get_neo4j_stats()
    print("\n知识图谱统计:")
    print(f"  总节点数: {stats.get('total_nodes', 0)}")
    print(f"  总关系数: {stats.get('total_relationships', 0)}")

    if stats.get("nodes"):
        print("\n  节点分布:")
        for label, count in sorted(stats["nodes"].items()):
            print(f"    {label}: {count}")

    if stats.get("relationships"):
        print("\n  关系分布:")
        for rel_type, count in sorted(stats["relationships"].items()):
            print(f"    {rel_type}: {count}")

    if stats.get("error"):
        print(f"\n  错误: {stats['error']}")


def cmd_test(_args):
    """Test Neo4j connection."""
    from .utils import test_neo4j_connection

    result = test_neo4j_connection()
    if result["success"]:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")


def cmd_clear(_args):
    """Clear the Neo4j database."""
    from .utils import clear_neo4j_database

    confirm = input("确认清空数据库? 此操作不可逆! (输入 YES 确认): ")
    if confirm == "YES":
        result = clear_neo4j_database()
        print(result["message"])
    else:
        print("操作已取消")


def main():
    parser = argparse.ArgumentParser(
        description="Ship Fault Knowledge Graph CLI",
        prog="python -m KnowledgeGraph.main",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # build
    build_parser = subparsers.add_parser("build", help="Build knowledge graph")
    build_parser.add_argument("--file", "-f", help="Build from a single file")
    build_parser.add_argument("--text", "-t", help="Build from raw text")
    build_parser.add_argument("--data-dir", "-d", help="Data directory path")
    build_parser.add_argument("--pattern", "-p", default="*.md", help="File glob pattern")
    build_parser.set_defaults(func=cmd_build)

    # query (RAG)
    query_parser = subparsers.add_parser("query", help="RAG query")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    query_parser.add_argument("--retriever", "-r", default="vector",
                              choices=["vector", "hybrid", "text2cypher"],
                              help="Retriever type")
    query_parser.set_defaults(func=cmd_query)

    # search (vector)
    search_parser = subparsers.add_parser("search", help="Vector search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    search_parser.set_defaults(func=cmd_search)

    # hybrid search
    hybrid_parser = subparsers.add_parser("hybrid", help="Hybrid search")
    hybrid_parser.add_argument("query", help="Search query")
    hybrid_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    hybrid_parser.set_defaults(func=cmd_hybrid)

    # text2cypher
    cypher_parser = subparsers.add_parser("cypher", help="Text2Cypher search")
    cypher_parser.add_argument("question", help="Natural language question")
    cypher_parser.set_defaults(func=cmd_cypher)

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show graph statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # test
    test_parser = subparsers.add_parser("test", help="Test Neo4j connection")
    test_parser.set_defaults(func=cmd_test)

    # clear
    clear_parser = subparsers.add_parser("clear", help="Clear database")
    clear_parser.set_defaults(func=cmd_clear)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
