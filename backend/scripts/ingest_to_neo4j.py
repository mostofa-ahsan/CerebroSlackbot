from neo4j import GraphDatabase
import json
import os

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
CHUNKED_DIR = "../data/chunked_text_files"

def ingest_data_to_neo4j(chunked_dir, uri, user, password):
    """Ingest chunks into Neo4j."""
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        for chunk_file in os.listdir(chunked_dir):
            if chunk_file.endswith(".json"):
                chunk_path = os.path.join(chunked_dir, chunk_file)
                with open(chunk_path, "r") as f:
                    chunks = json.load(f)
                for chunk in chunks:
                    session.run(
                        """
                        CREATE (c:Chunk {chunk_id: $chunk_id, text: $text})
                        WITH c
                        UNWIND $links AS link
                        CREATE (l:Link {url: link})
                        CREATE (c)-[:HAS_LINK]->(l)
                        """,
                        chunk_id=chunk["chunk_id"], text=chunk["text"], links=chunk["links"]
                    )
    print("Data ingested into Neo4j!")

if __name__ == "__main__":
    ingest_data_to_neo4j(CHUNKED_DIR, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
