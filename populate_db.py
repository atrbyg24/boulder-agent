import sqlite3
import requests

# The endpoint and query we've built
URL = "https://api.openbeta.io"
QUERY = """
query GetArea($id: ID!) {
  area(uuid: $id) {
    areaName
    metadata { lat lng }
    children { uuid areaName }
    climbs {
      uuid
      name
      content { description }
      grades { vscale }
      type { bouldering }
    }
  }
}
"""

def ingest_node(area_id, levels, conn, p_lat=None, p_lng=None):
    response = requests.post(URL, json={'query': QUERY, 'variables': {'id': area_id}})
    data = response.json().get('data', {}).get('area', {})
    if not data:
        print(f"No data found for ID: {area_id}")
        return

    # Use this level's GPS, or fall back to parent's
    metadata = data.get('metadata', {})
    current_lat = metadata.get('lat') if metadata.get('lat') else p_lat
    current_lng = metadata.get('lng') if metadata.get('lng') else p_lng

    current_name = data['areaName']
    current_levels = levels + [current_name]
    
    cursor = conn.cursor()
    for climb in data.get('climbs', []):
        if climb['type']['bouldering']:
            # Hierarchy mapping: [Area, SubArea, Crag, Rock]
            h = current_levels
            row = (
                climb['uuid'],
                h[0] if len(h) > 0 else None, # Area
                h[1] if len(h) > 1 else None, # Sub Area
                h[2] if len(h) > 2 else None, # Crag
                h[3] if len(h) > 3 else None, # Rock
                climb['name'],
                f"V{climb['grades']['vscale']}" if climb['grades']['vscale'] is not None else "V?",
                climb.get('content', {}).get('description', ""),
                current_lat, current_lng
            )
            cursor.execute("""
                INSERT OR IGNORE INTO boulders 
                (uuid, area, sub_area, crag, rock, name, grade, description, lat, lng) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
    
    conn.commit()
    print(f"Processed: {' > '.join(current_levels)}")

    # Keep going down into Crags and Rocks
    for child in data.get('children', []):
        ingest_node(child['uuid'], current_levels, conn, current_lat, current_lng)

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    conn = sqlite3.connect('data/routes.db')
    
    # 1. Create the table
    conn.execute('''CREATE TABLE IF NOT EXISTS boulders 
                   (uuid TEXT PRIMARY KEY, area TEXT, sub_area TEXT, crag TEXT, 
                    rock TEXT, name TEXT, grade TEXT, description TEXT, 
                    lat REAL, lng REAL)''')

    # 2. Define our targets
    # Format: (Target UUID, Starting Hierarchy List)
    locations = [
        ("92aa8885-6ff6-5eaf-bb8c-b93b1f257082", ["Powerlinez"]),
        ("593b4f6d-7419-58b2-8ed5-671c61fc726e", ["Gunks"]), # Trapps Bouldering
        ("f4236a26-3d60-5f21-9922-a982992d9f7a", ["Gunks"]), # Near Trapps Bouldering
        ("3e31e342-9908-5969-8082-f5a709280d90", ["Gunks"])  # Peterskill Bouldering
    ]

    # 3. Run Ingestion
    for uuid, path in locations:
        print(f"--- Starting Ingestion for {path[-1]} ---")
        ingest_node(uuid, path, conn)

    conn.close()
    print("--- All Database Populations Complete ---")