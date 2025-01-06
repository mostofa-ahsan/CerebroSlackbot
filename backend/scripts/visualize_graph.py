from pyvis.network import Network
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def fetch_graph_data():
    """Fetch graph data from Neo4j."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    nodes = []
    edges = []

    with driver.session() as session:
        result = session.run("""
            MATCH (p:Page)-[:LINKS_TO]->(c:Page)
            RETURN p.link AS source, c.link AS target
            """)
        for record in result:
            nodes.append(record["source"])
            edges.append((record["source"], record["target"]))

    return nodes, edges

def visualize_graph():
    """Visualize the graph."""
    nodes, edges = fetch_graph_data()
    net = Network(height="750px", width="100%", directed=True)

    for node in set(nodes):
        net.add_node(node)

    for source, target in edges:
        net.add_edge(source, target)

    net.show("graph.html")

if __name__ == "__main__":
    visualize_graph()

