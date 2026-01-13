
import os
import time
import streamlit as st
from google.api_core import exceptions
from google.genai import Client, types
from dotenv import load_dotenv
from db_tool import get_coordinates, run_sql_query
from weather_tool import get_bouldering_weather

SYSTEM_PROMPT = """

You are a specialized Bouldering guidebook. 
You have no memory or knowledge of bouldering routes, grades, or weather. 

STRICT RULES:
1. You MUST NOT answer any factual questions from memory. 
2. For every user query, you MUST first call run_sql_query to fetch data or get_coordinates for location data. 
3. If the database returns no results, state 'I cannot find that in my database' rather than guessing."

TOOLS:
1. DATA: Use 'run_sql_query' for counts/lists (table: 'boulders', columns: name, grade, area, sub_area, crag, rock, lat, lng).
2. WEATHER: To check if it is dry/climbable:
   a. Call 'get_coordinates' to get lat/lng.
   b. If coordinates are returned, call 'get_bouldering_weather'.
   c. If 'ambiguous' is returned, ask the user which location they meant.
3. LOGIC: 
   - 'Green' = Sending temps (35-60F) and dry.
   - 'Yellow' = Safe but sub-optimal (warm/humid).
   - 'Red' = Wet rock (seepage) or dangerous weather.
"""

@st.cache_resource
def get_agent_instance():
    """Initializes the model once and keeps it in memory."""
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    model_id = "gemini-2.5-flash-lite" 
    
    tools = [run_sql_query, get_bouldering_weather]
    
    chat = client.chats.create(
        model=model_id,
        config=types.GenerateContentConfig(
            tools=tools,
            system_instruction=SYSTEM_PROMPT
        )
    )
    return chat

def process_query(prompt, status_callback):
    """Sends the prompt to Gemini and handles the response logic."""
    chat = get_agent_instance()
    
    status_callback.write("Querying the boulder-agent...")
    
    response = chat.send_message(prompt)
    
    # Track if tools were called for observability
    for part in response.candidates[0].content.parts:
        if part.function_call:
            status_callback.write(f"Executing tool: {part.function_call.name}")
            
    return response.text