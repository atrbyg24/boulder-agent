
import os
import time
import json
import datetime
from google.api_core import exceptions
from google.genai import Client, types
from dotenv import load_dotenv
from db_tool import get_coordinates, run_sql_query
from weather_tool import get_bouldering_weather


def log_trace(user_input, response):
    """Saves the AI's thought process and tool calls to a local file."""
    trace_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_query": user_input,
        "tool_calls": [],
        "final_answer": response.text
    }
    
    # Extract function calls from the response object
    for part in response.candidates[0].content.parts:
        if part.function_call:
            trace_entry["tool_calls"].append({
                "function": part.function_call.name,
                "args": part.function_call.args
            })
            
    with open("traces.jsonl", "a") as f:
        f.write(json.dumps(trace_entry) + "\n")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


client = Client(api_key=api_key)
tools = [get_coordinates, run_sql_query, get_bouldering_weather]


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


config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=tools,
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode="ANY", 
        )
    )
)
print("--- Bouldering Trip Planner Active ---")


chat = client.chats.create(model="gemini-2.5-flash", config=config)

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    for attempt in range(3):
        try:
            response = chat.send_message(user_input)
            log_trace(user_input, response)
            print(f"Agent: {response.text}")
            break 
        except exceptions.ResourceExhausted:
            print(f"  [Quota hit] Waiting {2**attempt}s to retry...")
            time.sleep(2**attempt + 1)
        except Exception as e:
            print(f"An error occurred: {e}")
            break    