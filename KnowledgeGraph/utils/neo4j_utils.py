"""
Neo4j Utility Functions

Helper functions for Neo4j database management, testing, and statistics.
"""
import logging
from neo4j import GraphDatabase

from ..config import Neo4jConfig

logger = logging.getLogger(__name__)


def test_neo4j_connection(
    uri: str = None,
    user: str = None,
    password: str = None,
) -> dict:
    """
    Test the connection to the Neo4j database.

    Returns:
        dict with 'success', 'message', and optional 'version' keys.
    """
    _uri = uri or Neo4jConfig.URI
    _user = user or Neo4jConfig.USER
    _password = password or Neo4jConfig.PASSWORD

    try:
        driver = GraphDatabase.driver(_uri, auth=(_user, _password))
        driver.verify_connectivity()

        with driver.session(database=Neo4jConfig.DATABASE) as session:
            result = session.run("CALL dbms.components() YIELD versions RETURN versions[0] AS version")
            version = result.single()["version"]

        driver.close()
        return {
            "success": True,
            "message": f"Connected to Neo4j (version {version})",
            "version": version,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {e}",
        }


def clear_neo4j_database(
    uri: str = None,
    user: str = None,
    password: str = None,
    database: str = None,
) -> dict:
    """
    Clear all nodes and relationships from the Neo4j database.

    WARNING: This operation is irreversible!

    Returns:
        dict with 'success' and 'message' keys.
    """
    _uri = uri or Neo4jConfig.URI
    _user = user or Neo4jConfig.USER
    _password = password or Neo4jConfig.PASSWORD
    _database = database or Neo4jConfig.DATABASE

    try:
        driver = GraphDatabase.driver(_uri, auth=(_user, _password))

        with driver.session(database=_database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            count_result = session.run("MATCH (n) RETURN count(n) AS count")
            remaining = count_result.single()["count"]

        driver.close()
        return {
            "success": True,
            "message": f"Database cleared. Remaining nodes: {remaining}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Clear failed: {e}",
        }


def get_neo4j_stats(
    uri: str = None,
    user: str = None,
    password: str = None,
    database: str = None,
) -> dict:
    """
    Get statistics about the Neo4j knowledge graph.

    Returns:
        dict with node counts by label and relationship counts by type.
    """
    _uri = uri or Neo4jConfig.URI
    _user = user or Neo4jConfig.USER
    _password = password or Neo4jConfig.PASSWORD
    _database = database or Neo4jConfig.DATABASE

    try:
        driver = GraphDatabase.driver(_uri, auth=(_user, _password))
        stats = {"nodes": {}, "relationships": {}, "total_nodes": 0, "total_relationships": 0}

        with driver.session(database=_database) as session:
            node_result = session.run(
                "MATCH (n) RETURN labels(n) AS labels, count(n) AS count"
            )
            for record in node_result:
                labels = record["labels"]
                count = record["count"]
                label_key = ":".join(sorted(labels)) if labels else "NO_LABEL"
                stats["nodes"][label_key] = count
                stats["total_nodes"] += count

            rel_result = session.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count"
            )
            for record in rel_result:
                rel_type = record["type"]
                count = record["count"]
                stats["relationships"][rel_type] = count
                stats["total_relationships"] += count

        driver.close()
        return stats
    except Exception as e:
        return {"error": str(e)}
