from neo4j import GraphDatabase
import networkx as nx
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def run_cypher_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record["p"] for record in result]

def neo4j_to_networkx(neo4j_paths):
    G = nx.Graph()
    
    for path in neo4j_paths:
        nodes = path.nodes
        relationships = path.relationships
        for relationship in relationships:
            G.add_edge(relationship.start_node["id"], relationship.end_node["id"], type=relationship.type)

    return G

relation_queries = {
    'Effects': "MATCH p=()-[:AFFECTS]->() RETURN p LIMIT 25;",
    'CAUSES': "MATCH p=()-[:CAUSES]->() RETURN p LIMIT 25;",
    'Integrates': "MATCH p=()-[:INTEGRATES]->() RETURN p LIMIT 25;",
    'Damages': "MATCH p=()-[:DAMAGES]->() RETURN p LIMIT 25;",
    'Effected-By': "MATCH p=()-[:AFFECTED_BY]->() RETURN p LIMIT 25;",
    'Impact': "MATCH p=()-[:IMPACTS]->() RETURN p LIMIT 25;",
    'Applies-To': "MATCH p=()-[:APPLIES_TO]->() RETURN p LIMIT 25;",
    'Funds': "MATCH p=()-[:FUNDS]->() RETURN p LIMIT 25;",
    'Contributes': "MATCH p=()-[:CONTRIBUTES_TO]->() RETURN p LIMIT 25;",
    'Developed': "MATCH p=()-[:DEVELOPED]->() RETURN p LIMIT 25;",
    'Governing': "MATCH p=()-[:GOVERNING]->() RETURN p LIMIT 25;",
    'Specifies': "MATCH p=()-[:SPECIFIES]->() RETURN p LIMIT 25;",
    'Promotes': "MATCH p=()-[:PROMOTES]->() RETURN p LIMIT 25;",
}

def get_graph(relation_option):
    query = relation_queries.get(relation_option)
    if query:
        neo4j_paths = run_cypher_query(query)
        return neo4j_to_networkx(neo4j_paths)
    return None
