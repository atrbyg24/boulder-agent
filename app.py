import streamlit as st
from boulder_engine import process_query

st.set_page_config(page_title="BoulderAgent", page_icon="🧗")
st.title("🧗 BoulderAgent")

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