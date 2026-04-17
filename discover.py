import os
import networkx as nx
from dotenv import load_dotenv
from specklepy.api.client import SpeckleClient
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
from collections import Counter
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
HOST = "app.speckle.systems"
TOKEN = os.getenv("SPECKLE_TOKEN")         
PROJECT_ID = "09d6ea6f13"           
ROOT_OBJ_ID = "cb3e354871571d23375937356acd0caf"  

print("Authenticating & Pulling...")
client = SpeckleClient(host=HOST)
client.authenticate_with_token(TOKEN)
transport = ServerTransport(stream_id=PROJECT_ID, client=client)
base_object = operations.receive(obj_id=ROOT_OBJ_ID, remote_transport=transport)

# --- THE DISCOVERY LOGIC ---
category_counts = Counter()

def profile_building_categories(obj):
    """Scans the building and tallies every single unique category or type."""
    if not hasattr(obj, "id") or not obj.id:
        return

    # Grab the Revit category if it exists
    category = getattr(obj, "category", None)
    
    if category:
        category_counts[f"[Category] {category}"] += 1
    else:
        # If it doesn't have a strict category, grab its Speckle Type
        obj_type = getattr(obj, "speckle_type", "Unknown").split('.')[-1]
        category_counts[f"[SpeckleType] {obj_type}"] += 1

    # Traverse children (same nested logic as the graph builder)
    dynamic_props = obj.get_dynamic_member_names() if hasattr(obj, 'get_dynamic_member_names') else []
    
    if hasattr(obj, "elements") and obj.elements:
        for child in obj.elements:
            profile_building_categories(child)
            
    for prop in dynamic_props:
        val = getattr(obj, prop)
        if isinstance(val, list):
            for item in val:
                if hasattr(item, "speckle_type"):
                    profile_building_categories(item)


print("Scanning building architecture...")
profile_building_categories(base_object)

print("\n--- MASTER CATEGORY LIST ---")
# Print them out sorted by most common to least common
for category, count in category_counts.most_common():
    print(f"{count:5} x {category}")