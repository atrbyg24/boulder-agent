
import os
import time
from google.api_core import exceptions
from google.genai import Client, types
from dotenv import load_dotenv
from db_tool import get_coordinates, run_sql_query
from weather_tool import get_bouldering_weather

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


client = Client(api_key=api_key)
tools = [get_coordinates, run_sql_query, get_bouldering_weather]


SYSTEM_PROMPT = """
You are a Bouldering Guide for NY/NJ. Use these tools to help users plan trips:

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
            print(f"Agent: {response.text}")
            break 
        except exceptions.ResourceExhausted:
            print(f"  [Quota hit] Waiting {2**attempt}s to retry...")
            time.sleep(2**attempt + 1)
        except Exception as e:
            print(f"An error occurred: {e}")
            break    