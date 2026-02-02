# from neo4j import GraphDatabase
# import networkx as nx
# import matplotlib.pyplot as plt

# class Neo4jGraphVisualizer:
#     def __init__(self, uri, username, password):
#         self.driver = GraphDatabase.driver(uri, auth=(username, password))

#     def close(self):
#         self.driver.close()

#     def run_query(self, cypher_query, parameters=None):
#         with self.driver.session() as session:
#             result = session.run(cypher_query, parameters or {})
#             return list(result)

#     @staticmethod
#     def build_graph(records):
#         G = nx.Graph()

#         for record in records:
#             for value in record.values():
#                 # Node handling
#                 if hasattr(value, "labels"):
#                     node_id = value.id
#                     G.add_node(
#                         node_id,
#                         labels=list(value.labels),
#                         properties=dict(value)
#                     )

#                 # Relationship handling
#                 elif hasattr(value, "type"):
#                     start = value.start_node.id
#                     end = value.end_node.id
#                     G.add_edge(
#                         start,
#                         end,
#                         label=value.type,
#                         properties=dict(value)
#                     )
#         return G

#     @staticmethod
#     def draw_graph(G, figsize=(14, 10)):
#         plt.figure(figsize=figsize)

#         pos = nx.spring_layout(G, seed=42)

#         node_labels = {
#             node: "\n".join(G.nodes[node].get("labels", [])) +
#                   "\n" +
#                   str(G.nodes[node].get("properties", {}).get("name", ""))
#             for node in G.nodes
#         }

#         edge_labels = {
#             (u, v): data.get("label", "")
#             for u, v, data in G.edges(data=True)
#         }

#         nx.draw(
#             G,
#             pos,
#             with_labels=True,
#             labels=node_labels,
#             node_size=2800,
#             node_color="lightblue",
#             font_size=9
#         )

#         nx.draw_networkx_edge_labels(
#             G,
#             pos,
#             edge_labels=edge_labels,
#             font_color="red",
#             font_size=8
#         )

#         plt.title("Neo4j Graph Visualization")
#         plt.axis("off")
#         plt.show()


# # -------------------------------
# # Example Usage
# # -------------------------------
# if __name__ == "__main__":
#     URI = "neo4j://172.52.50.179:7687"
#     USERNAME = "neo4j"
#     PASSWORD = "password"

#     QUERY = """
#     MATCH (dr:Drug)-[t:TREATS]->(d:Disease) WHERE toLower(d.name) = "lung cancer"
#     RETURN dr, t, d LIMIT 10
#     """

#     visualizer = Neo4jGraphVisualizer(URI, USERNAME, PASSWORD)
#     records = visualizer.run_query(QUERY)
#     graph = visualizer.build_graph(records)
#     visualizer.draw_graph(graph)
#     visualizer.close()