import sys
import os
import toml
import re
from unittest.mock import MagicMock

mock_st = MagicMock()
def identity_decorator(func): return func
mock_st.cache_resource = identity_decorator
mock_st.cache_data = identity_decorator

# Load secrets from local toml
secrets_path = ".streamlit/secrets.toml"
if os.path.exists(secrets_path):
    with open(secrets_path, "r") as f:
        mock_st.secrets = toml.load(f)
else:
    mock_st.secrets = {"GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY")}

sys.modules["streamlit"] = mock_st

try:
    import boulder_engine
except ImportError as e:
    print(f"Failed to import boulder_engine: {e}")
    sys.exit(1)


def run_test(test_name, query, expected_tools_sequence):
    """
    Runs a query and validates:
    1. The correct tools were called.
    2. The tools were called in the correct order.
    3. The data passed between chained tools is identical (no hallucinations).
    """
    print(f"\n{'='*60}")
    print(f"TEST CASE: {test_name}")
    print(f"QUERY: \"{query}\"")
    print(f"{'='*60}")
    
    # Get a fresh chat session
    chat = boulder_engine.get_chat_session()
    
    try:
        response = chat.send_message(query)
    except Exception as e:
        print(f"❌ EXECUTION ERROR: {e}")
        return

    actual_tools = []
    tool_inputs = {}  # Store what the model sent to the tool
    tool_outputs = {} # Store what the tool gave back to the model

    for message in chat.history:
        # Capture what the model DECIDED to do
        if message.role == "model":
            for part in message.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    name = part.function_call.name
                    args = dict(part.function_call.args)
                    actual_tools.append(name)
                    tool_inputs[name] = args
        
        # Capture what the tool actually RETURNED
        if message.role == "function" or (hasattr(message, "parts") and message.parts[0].function_response):
            part = message.parts[0]
            if part.function_response:
                res_name = part.function_response.name
                res_content = part.function_response.response
                tool_outputs[res_name] = res_content

    print(f"Captured Tool Sequence: {actual_tools}")

    
    it = iter(actual_tools)
    sequence_passed = all(tool in it for tool in expected_tools_sequence)
    
    if sequence_passed:
        print("✅ PASS: Tool chain sequence is correct.")
        
        # Did the lat/lng from get_coordinates match the input to weather?
        if "get_coordinates" in actual_tools and "get_bouldering_weather" in actual_tools:
            output_data = tool_outputs.get("get_coordinates")
            input_data = tool_inputs.get("get_bouldering_weather")

            if output_data and input_data:
                # Compare lat and lng
                # Using round() because LLMs sometimes truncate 41.12345 to 41.123
                out_lat, out_lng = output_data.get('lat'), output_data.get('lng')
                in_lat, in_lng = input_data.get('lat'), input_data.get('lng')
                
                if out_lat == in_lat and out_lng == in_lng:
                    print("✅ PASS: Data integrity maintained. Lat/Lng passed correctly.")
                else:
                    print(f"❌ FAIL: Data mismatch in handshake!")
                    print(f"   Coordinates Tool returned: lat={out_lat}, lng={out_lng}")
                    print(f"   Weather Tool received:    lat={in_lat}, lng={in_lng}")
            else:
                print("❌ FAIL: Could not find tool output/input data for validation.")
    else:
        print(f"❌ FAIL: Sequence mismatch.")
        print(f"   Expected: {expected_tools_sequence}")
        print(f"   Actual:   {actual_tools}")

    if response.text and len(response.text) > 10:
        print("✅ PASS: Model generated a final text response.")
    else:
        print("❌ FAIL: Model failed to generate a final summary.")


def main():
    print("Starting Offline Evaluation Suite...")
    
    run_test(
        test_name="Basic SQL Search",
        query="List the names of all boulders in 'The Trapps'.",
        expected_tools_sequence=["run_sql_query"]
    )
    
    run_test(
        test_name="Weather Dependency Chain",
        query="What is the weather like at Powerlinez today?",
        expected_tools_sequence=["get_coordinates", "get_bouldering_weather"]
    )
    
    run_test(
        test_name="Unknown Location Weather",
        query="What's the weather like on Mars Boulders?",
        expected_tools_sequence=["get_coordinates"] # Should call coords, find nothing, and stop.
    )

if __name__ == "__main__":
    main()