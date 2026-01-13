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

def ingest_node(area_id: str, levels: list[str], conn: sqlite3.Connection, p_lat: float = None, p_lng: float = None):
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
            grade = climb['grades']['vscale']
            if grade is None:
                grade = "V?"
            # Hierarchy mapping: [Area, SubArea, Crag, Rock]
            h = current_levels
            row = (
                climb['uuid'],
                h[0] if len(h) > 0 else None, # Area
                h[1] if len(h) > 1 else None, # Sub Area
                h[2] if len(h) > 2 else None, # Crag
                h[3] if len(h) > 3 else None, # Rock
                climb['name'],
                grade,
                current_lat, current_lng
            )
            cursor.execute("""
                INSERT OR IGNORE INTO boulders 
                (uuid, area, sub_area, crag, rock, name, grade, lat, lng) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
    
    conn.commit()
    print(f"Processed: {' > '.join(current_levels)}")

    # Keep going down into Crags and Rocks
    for child in data.get('children', []):
        ingest_node(child['uuid'], current_levels, conn, current_lat, current_lng)

if __name__ == "__main__":
    conn = sqlite3.connect('data/routes.db')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS boulders 
                   (uuid TEXT PRIMARY KEY, area TEXT, sub_area TEXT, crag TEXT, 
                    rock TEXT, name TEXT, grade TEXT, description TEXT, 
                    lat REAL, lng REAL)''')

    # Format: (Target UUID, Starting Hierarchy List)
    locations = [
        ("92aa8885-6ff6-5eaf-bb8c-b93b1f257082", ["Powerlinez"]), # Powerlinez Bouldering
        ("ac0a626a-495a-57b9-99f0-b9a0687b3f97", ["Gunks"]), # Trapps Bouldering
        ("f41fc434-c60f-517e-95b7-0b76e0978b5d", ["Gunks"]), # Near Trapps Bouldering
        ("150dc369-9adc-5633-b3ab-39d2a291d503", ["Gunks"])  # Peterskill Bouldering
    ]

    for uuid, path in locations:
        print(f"--- Starting Ingestion for {path[-1]} ---")
        ingest_node(uuid, path, conn)

    conn.close()
    print("--- All Database Populations Complete ---")