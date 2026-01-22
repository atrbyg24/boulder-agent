import streamlit as st
from boulder_engine import process_query
import base64

st.set_page_config(page_title="BoulderAgent", page_icon="🧗")

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = "art-litvinau-F6-HLw_R7t4-unsplash.jpg"
img_base64 = get_img_as_base64(img_path)

page_bg_img = f'''
<style>
[data-testid="stAppViewContainer"] {{
    background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
}}
[data-testid="stHeader"] {{
    background-color: rgba(0,0,0,0);
}}
[data-testid="stVerticalBlock"] > div:has(div.stChatFloatingInputContainer) {{
    background: rgba(255, 255, 255, 0.8);
    padding: 2rem;
    border-radius: 15px;
}}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

st.title("🧗 BoulderAgent")

with st.sidebar:
    st.markdown("""
        **Data Sources:** [OpenBeta](https://openbeta.io) & [Open-Meteo](https://open-meteo.com)
        
        *Currently supporting: **The Powerlinez** and **The Gunks***
    """)
    st.markdown('Photo by <a href="https://unsplash.com/@umate?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Art Litvinau</a> on <a href="https://unsplash.com/photos/a-large-rock-formation-in-the-middle-of-a-desert-F6-HLw_R7t4?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>', unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

st.divider()

# Manage conversation history in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Suggested Queries
if not st.session_state.messages:
    st.markdown("### Suggested Queries")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌦️ Weather at The Gunks?"):
            st.session_state.messages.append({"role": "user", "content": "How is the weather at The Gunks?"})
            st.rerun()
    with col2:
        if st.button("🪨 Boulders in Powerlinez V3-V5"):
            st.session_state.messages.append({"role": "user", "content": "Find me boulders in Powerlinez rated V3-V5"})
            st.rerun()

# User input
if prompt := st.chat_input("Ask a question about bouldering..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Generate response if last message is from user
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=True) as status:
            full_response = process_query(st.session_state.messages[-1]["content"], status)
            status.update(label="Response generated!", state="complete", expanded=False)
        
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

