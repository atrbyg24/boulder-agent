import datetime
import json
import streamlit as st
from google.genai import Client, types
from db_tool import get_coordinates, run_sql_query
from weather_tool import get_bouldering_weather

SYSTEM_PROMPT = """
You are a local bouldering expert and guide. 
You have no internal memory of specific bouldering routes, grades, or weather. 

STRICT RULES:
1. You MUST NOT answer any factual questions from memory. 
2. For every query, you MUST use tools to fetch data. Never guess.
3. If no results are found after trying multiple tools, state 'I cannot find that in my database.'

DATABASE SCHEMA:
- Table 'areas': Contains general climbing regions and sub-areas. 
  Columns: [uuid, name, lat, lng, parent_name]
  Use this for: "How is the weather at Powerlinez?" or "Where is the Trapps?"
  
- Table 'boulders': Contains specific bouldering routes and rocks. 
  Columns: [uuid, area, sub_area, crag, rock, name, grade, lat, lng]
  Use this for: "Where is the climb 'Paul Bunyan'?" or "List V3s in Peterskill."

TOOLS & WORKFLOW:
1. COORDINATES (Geocoding): 
   - To find weather or a location, call 'get_coordinates'.
   - This tool is smart: it checks 'areas' first, then 'boulders'.
2. DATA: 
   - Use 'run_sql_query' for specific lists (e.g., "Show me all V4s").
3. WEATHER: 
    - You MUST NEVER call 'get_bouldering_weather' unless you have lat/lng.
    - You MUST call 'get_coordinates' first to get lat/lng.
    - Once you have lat/lng, call 'get_bouldering_weather'.

RESPONSE GUIDELINES:
- Always report Temperature and Humidity in your summary.
- Follow this format: [Status Color] + [Detailed conditions].

LOGIC: 
- 'Green' = Sending temps (35-60F) and dry rock.
- 'Yellow' = Safe but greasy (humidity > 70% or temp > 60F).
- 'Red' = Wet rock, rain, or dangerous heat.

EXAMPLE RESPONSE:
"The conditions at Powerlinez are **Green**! It's currently a crisp 45°F with 35% humidity—perfect friction. No rain is reported, so the rock should be dry."
"""

@st.cache_resource
def get_agent_instance():
    """Initializes the model once and keeps it in memory."""
    client = Client(api_key=st.secrets["GEMINI_API_KEY"])
    model_id = "gemini-2.5-flash-lite" 
    
    tools = [run_sql_query, get_coordinates, get_bouldering_weather]
    
    agent_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools,
        # Automatic function calling handles the chain (Coords -> Weather)
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=False
        ),
        # Forced function calling ensures the agent doesn't "lazily" ignore tools
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY", 
                allowed_function_names=["run_sql_query", "get_coordinates", "get_bouldering_weather"]
            )
        )
    )
    
    chat = client.chats.create(
        model=model_id,
        config=agent_config
    )
    return chat


def process_query(prompt, status_callback):
    """Sends the prompt to Gemini and handles the response logic."""
    chat = get_agent_instance()
    
    status_callback.write("Querying the boulder-agent...")
    
    response = chat.send_message(prompt)

    trace_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_query": prompt,
        "tool_calls": [],
        "final_answer": response.text
    }
    
    for part in response.candidates[0].content.parts:
        if part.function_call:
            call_data = {
                "function": part.function_call.name,
                "args": part.function_call.args
            }
            trace_entry["tool_calls"].append(call_data)
            
            status_callback.write(f"🛠️ **Calling Tool:** `{call_data['function']}`")
            status_callback.write(f"Parameters: `{call_data['args']}`")

    with open("traces.jsonl", "a") as f:
        f.write(json.dumps(trace_entry) + "\n")
            
    return response.text