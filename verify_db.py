import sqlite3

def verify_data():
    conn = sqlite3.connect('data/routes.db')
    cursor = conn.cursor()

    print("--- Database Sanity Check ---")

    # 1. Total Count
    cursor.execute("SELECT COUNT(*) FROM boulders")
    print(f"Total Boulders Ingested: {cursor.fetchone()[0]}")

    # 2. Check Hierarchy Distribution
    print("\n--- Breakdown by Area and Sub-Area ---")
    cursor.execute("""
        SELECT area, sub_area, COUNT(*) 
        FROM boulders 
        GROUP BY area, sub_area
    """)
    for area, sub_area, count in cursor.fetchall():
        print(f"[{area}] -> {sub_area}: {count} boulders")

    # 3. Check Coordinate Coverage
    cursor.execute("SELECT COUNT(*) FROM boulders WHERE lat IS NULL OR lng IS NULL")
    missing_gps = cursor.fetchone()[0]
    print(f"\nBoulders missing GPS: {missing_gps}")

    # 4. Preview a specific "Problem Child" (e.g., Gunks)
    print("\n--- Previewing first 5 Gunks Boulders ---")
    cursor.execute("""
        SELECT name, sub_area, crag, rock, grade, description,lat, lng 
        FROM boulders 
        WHERE area = 'Powerlinez' 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    verify_data()