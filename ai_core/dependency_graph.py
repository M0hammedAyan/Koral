def build_graph(edges):

    # collect all unique nodes
    nodes = list(set(
        [e["source"] for e in edges] +
        [e["target"] for e in edges]
    ))

    return {
        "nodes": nodes,
        "edges": edges
    }