import sqlite3

DB_PATH = 'data/routes.db'

def get_coordinates(location_name: str, location_type: str | None = "rock", parent_area: str | None = None) -> dict | None:
    """
    Retrieves the latitude and longitude for a specific location.

    This function searches for coordinates involves checking for duplicate names
    and providing disambiguation options if necessary.

    Args:
        location_name: The name of the rock, climb, or location to search for.
        location_type: The column to search against (e.g., 'rock', 'name'). Defaults to "rock".
        parent_area: An optional filter (e.g., 'Peterskill') used to narrow down results
                     and resolve naming conflicts.

    Returns:
        dict: A dictionary containing 'lat' and 'lng' if a unique location is found.
              If multiple matches are found, returns a dictionary with 'ambiguous': True
              and a list of 'options'.
        None: If no matching location is found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Base query
    query = f"SELECT lat, lng, rock, sub_area, area FROM boulders WHERE {location_type} LIKE ?"
    params = [f"%{location_name}%"]
    
    # Add optional parent filtering to resolve duplicates
    if parent_area:
        query += " AND (area LIKE ? OR sub_area LIKE ?)"
        params.extend([f"%{parent_area}%", f"%{parent_area}%"])
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    if len(results) == 1:
        return {"lat": results[0][0], "lng": results[0][1]}
    
    if len(results) > 1:
        # Return a list of options so the Agent can ask the user for clarification
        return {
            "ambiguous": True,
            "options": [{"rock": r[2], "sub_area": r[3], "area": r[4]} for r in results]
        }
        
    return None

def run_sql_query(sql_query: str) -> list:
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