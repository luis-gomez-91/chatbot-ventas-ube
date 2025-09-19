import streamlit as st
from agent import initialize_agent

st.set_page_config(page_title="Word Chatbot", page_icon="🤖")
st.title("🤖 Word Dictionary Chatbot")
st.markdown("Chat with an AI assistant that knows the meanings of words.")

agent = initialize_agent()

if not agent:
    st.error("Agent could not be initialized. Please check your environment variables.")
else:
    # Inicializar historial de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar mensajes existentes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de usuario
    if prompt := st.chat_input("Ask about a word..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                from argo.client import stream
                response_generator = stream(agent, prompt)
                full_response = st.write_stream(response_generator)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
