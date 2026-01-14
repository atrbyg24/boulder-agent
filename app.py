import streamlit as st
from boulder_engine import process_query
import base64

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "art-litvinau-F6-HLw_R7t4-unsplash.jpg"
img_base64 = get_img_as_base64(img_path)

page_bg_img = f'''
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
}}
[data-testid="stHeader"] {{
    background-color: rgba(0,0,0,0);
}}
/* This makes the main container semi-transparent for readability */
[data-testid="stVerticalBlock"] > div:has(div.stChatFloatingInputContainer) {{
    background: rgba(255, 255, 255, 0.8);
    padding: 2rem;
    border-radius: 15px;
}}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)
st.markdown('Photo by <a href="https://unsplash.com/@umate?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Art Litvinau</a> on <a href="https://unsplash.com/photos/a-large-rock-formation-in-the-middle-of-a-desert-F6-HLw_R7t4?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>', unsafe_allow_html=True)


st.set_page_config(page_title="BoulderAgent", page_icon="🧗")
st.title("🧗 BoulderAgent")
st.markdown("""
    **Data Sources:** [OpenBeta](https://openbeta.io) & [Open-Meteo](https://open-meteo.com)
    
    *Currently supporting: **The Powerlinez** and **The Gunks***
""")
st.divider()

# Manage conversation history in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How's the weather at Powerlinez?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # The 'status' block is where we see the tool calls live
        with st.status("Thinking...", expanded=True) as status:
            full_response = process_query(prompt, status)
            status.update(label="Response generated!", state="complete", expanded=False)
        
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})