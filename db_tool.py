import sqlite3

DB_PATH = 'data/routes.db'

def get_coordinates(location_name: str, location_type: str | None = None, parent_area: str | None = None) -> dict | None:
    """
    Retrieves the latitude and longitude for a specific location.

    This function searches for coordinates in the 'areas' and 'boulders' tables.
    It supports filtering by location type and handles ambiguity by returning a list of options
    if multiple matches are found (unless a unique Area match is found first).

    Args:
        location_name: The name of the rock, climb, or location to search for.
        location_type: Optional filter. If "area", searches only areas.
                       If "rock", "boulder", or "climb", searches only boulders.
                       Defaults to None (searches both).
        parent_area: An optional filter (e.g., 'Peterskill') used to narrow down results
                     and resolve naming conflicts.

    Returns:
        dict: A dictionary containing 'lat', 'lng', and 'type' if a unique location is found.
              If multiple matches are found, returns a dictionary with 'ambiguous': True
              and a list of 'options'.
        None: If no matching location is found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Determine what to search based on location_type
    search_areas = not location_type or location_type.lower() in ["area", "location"]
    search_boulders = not location_type or location_type.lower() in ["rock", "boulder", "climb", "route", "point"]

    area_results = []
    if search_areas:
        area_query = "SELECT lat, lng, name, parent_name FROM areas WHERE name LIKE ?"
        area_params = [f"%{location_name}%"]

        if parent_area:
            area_query += " AND parent_name LIKE ?"
            area_params.append(f"%{parent_area}%")

        cursor.execute(area_query, area_params)
        area_results = cursor.fetchall()

        if len(area_results) == 1:
            conn.close()
            return {"lat": float(area_results[0][0]), "lng": float(area_results[0][1]), "type": "area"}

    boulder_results = []
    if search_boulders:
        # This captures specific climbs or rocks if the area search was empty or too broad
        boulder_query = "SELECT lat, lng, name, area, sub_area FROM boulders WHERE name LIKE ?"
        boulder_params = [f"%{location_name}%"]

        if parent_area:
            boulder_query += " AND (area LIKE ? OR sub_area LIKE ?)"
            boulder_params.extend([f"%{parent_area}%", f"%{parent_area}%"])

        cursor.execute(boulder_query, boulder_params)
        boulder_results = cursor.fetchall()

    conn.close()

    # Combine results to check for total ambiguity
    total_matches = area_results + boulder_results

    if not total_matches:
        return None

    if len(total_matches) == 1:
        res = boulder_results[0] if boulder_results else area_results[0]
        return {"lat": float(res[0]), "lng": float(res[1]), "type": "point"}

    options = []
    for r in area_results:
        options.append({"name": r[2], "context": r[3], "category": "Area"})
    for r in boulder_results:
        options.append({"name": r[2], "context": f"{r[3]} > {r[4]}", "category": "Climb/Rock"})

    return {
        "ambiguous": True,
        "options": options
    }

    
def run_sql_query(sql_query: str) -> list:
    """
    Executes a read-only SQL query against the boulders database.
    The database has two tables:
    1. 'areas': Use this for general location lookups (e.g., Powerlinez, Gunks, Peterskill).
       Columns: uuid, name, lat, lng, parent_name
    2. 'boulders': Use this for specific route info (grades, specific climb names).
       Columns: uuid, area, sub_area, crag, rock, name, grade, lat, lng

    Args:
        sql_query (str): A valid SQLite SELECT statement.
    
    Returns:
        list: A list of dictionaries representing the rows from the database.
              Returns a list containing a dictionary with an "error" key if an exception occurs.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        return [{"error": str(e)}]
    finally:
        conn.close()