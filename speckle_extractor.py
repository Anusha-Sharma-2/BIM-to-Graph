import os
import networkx as nx
from dotenv import load_dotenv
from specklepy.api.client import SpeckleClient
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
import matplotlib.pyplot as plt

load_dotenv()

HOST = "app.speckle.systems"
TOKEN = os.getenv("SPECKLE_TOKEN")
PROJECT_ID = "09d6ea6f13"
VERSION_ID = "ed3daff416"
ROOT_OBJ_ID = "62d7a1c47777182e4a81bca0aff0512e"

# auth
print("Authenticating with Speckle")
client = SpeckleClient(host=HOST)
client.authenticate_with_token(TOKEN)

# geting data
print("Pulling building data")
transport = ServerTransport(stream_id=PROJECT_ID, client=client)
base_object = operations.receive(obj_id=ROOT_OBJ_ID, remote_transport=transport)

# directed graph
G = nx.DiGraph()

# Words we want to completely ignore to clean up the graph
IGNORE_LIST = ["Mesh", "RenderMaterial", "Material", "LevelProxy"]

def get_real_bim_name(obj):
    """Digs past Speckle's wrappers to find the actual architectural term."""
    # Look for explicit category tags first
    if hasattr(obj, "category") and obj.category:
        return f"[{obj.category}] {getattr(obj, 'name', '')[:15]}"
    
    # If it's a Revit/IFC element, the type usually contains the good stuff
    obj_type = getattr(obj, 'speckle_type', 'Unknown').split('.')[-1]
    name = getattr(obj, 'name', '')
    
    # If it's a proxy, try to signify it points to a real object
    if "Instance" in obj_type:
        return f"[HVAC Part] {name[:10]}" if name else "[HVAC Instance]"
        
    return f"[{obj_type}] {name[:10]}"

def traverse_and_build_graph(obj, parent_id=None):
    if not hasattr(obj, "id") or not obj.id:
        return

    obj_type = getattr(obj, "speckle_type", "UnknownElement")
    
    # FILTER: If it's a useless 3D mesh or material, stop traversing this branch!
    if any(ignore_word in obj_type for ignore_word in IGNORE_LIST):
        return
    
    node_id = obj.id
    
    # --- GET THE REAL SEMANTICS ---
    real_name = get_real_bim_name(obj)
        
    G.add_node(node_id, label=real_name)

    if parent_id:
        G.add_edge(parent_id, node_id, relationship="hosts")

    dynamic_props = obj.get_dynamic_member_names() if hasattr(obj, 'get_dynamic_member_names') else []
    
    if hasattr(obj, "elements") and obj.elements:
        for child in obj.elements:
            traverse_and_build_graph(child, parent_id=node_id)
            
    for prop in dynamic_props:
        val = getattr(obj, prop)
        if isinstance(val, list):
            for item in val:
                if hasattr(item, "speckle_type"):
                    traverse_and_build_graph(item, parent_id=node_id)

# --- 4. EXECUTE & VERIFY ---
print("Building the spatial graph...")
traverse_and_build_graph(base_object)

print("\n--- GRAPH EXTRACTION COMPLETE ---")
print(f"Total Nodes (Lego Blocks): {G.number_of_nodes()}")
print(f"Total Edges (Connections): {G.number_of_edges()}")

print("\nSample Semantic Relationships:")
# Print the first 15 edges with their REAL names
edge_sample = list(G.edges())[:15]
for u, v in edge_sample:
    u_label = G.nodes[u].get('label', 'Unknown')
    v_label = G.nodes[v].get('label', 'Unknown')
    # Truncate long names for the terminal printout
    print(f"{u_label[:30]:<30} --hosts--> {v_label[:30]}")

# --- 5. VISUALIZE A CHUNK ---
print("\nGenerating Visualization...")
# Instead of the root, let's find an actual "Collection" node that has children
# to act as the center of our mini-graph.
central_node = None
for n in G.nodes():
    if G.out_degree(n) > 5 and G.out_degree(n) < 30: # Find a folder with 5-30 items
        central_node = n
        break

if central_node:
    # Pluck out just this small neighborhood
    sub_nodes = list(nx.single_source_shortest_path_length(G, central_node, cutoff=2).keys())
    sub_G = G.subgraph(sub_nodes)

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(sub_G, k=0.5, iterations=50) 
    
    # Clean labels
    labels = {n: sub_G.nodes[n].get('label', '') for n in sub_G.nodes()}

    nx.draw(sub_G, pos, 
            with_labels=True, 
            labels=labels, 
            node_size=2000, 
            node_color="lightgreen", 
            font_size=9, 
            font_weight="bold",
            edge_color="gray",
            arrows=True)

    plt.title("Pruned Semantic BIM Sub-Graph", fontsize=16)
    plt.show()
else:
    print("Could not find a clean cluster.")