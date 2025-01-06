from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def create_graph_driver():
    """Connect to the Neo4j database."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def ingest_data_to_neo4j(metadata_file):
    """Ingest metadata into Neo4j."""
    driver = create_graph_driver()

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    with driver.session() as session:
        for entry in metadata:
            session.run("""
                MERGE (page:Page {id: $id, link: $link})
                WITH page
                UNWIND $child_links AS child_link
                MERGE (child:Page {link: child_link})
                MERGE (page)-[:LINKS_TO]->(child)
                """, id=entry["page_id"], link=entry["page_link"], child_links=entry["child_links"])
    print("Ingestion to Neo4j completed!")

if __name__ == "__main__":
    ingest_data_to_neo4j("../data/mapped_metadata.json")
