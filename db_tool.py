import sqlite3

DB_PATH = 'data/routes.db'

def get_coordinates(location_name: str, location_type: str = "rock"):
    """
    Fetches the latitude and longitude for a specific location.
    The AI uses this to provide coordinates to the weather_tool.

    Args:
        location_name (str): The name of the rock, crag, sub-area, or area.
        location_type (str): The column to search in ('rock', 'crag', 'sub_area', 'area').
    
    Returns:
        dict: {'lat': float, 'lng': float} or None if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Using 'LIKE' allows for slightly "fuzzy" matching
    query = f"SELECT lat, lng FROM boulders WHERE {location_type} LIKE ? LIMIT 1"
    cursor.execute(query, (f"%{location_name}%",))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] is not None:
        return {"lat": result[0], "lng": result[1]}
    return None

def run_sql_query(sql_query: str):
    """
    Executes a read-only SQL query against the boulders database.
    Use this to answer questions about counts, grades, and location lists.

    Args:
        sql_query (str): A valid SQLite SELECT statement.
    
    Returns:
        list: A list of rows (tuples) from the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()