import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Add parent directory to sys.path so we can import agent_logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agent_logic

st.set_page_config(page_title="Agentic RAG", page_icon="🤖", layout="wide")
load_dotenv()

# Get Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")

st.title("🤖 Agentic AI Document Explorer")
st.markdown("Upload your enterprise documents (PDF, TXT, CSV, Excel) and use our Agentic AI to query them!")

if not api_key:
    st.error("Please configure your GEMINI_API_KEY in the .env file or environment variables.")
    st.stop()

# Sidebar for Document Processing
with st.sidebar:
    st.header("1. Document Ingestion")
    uploaded_files = st.file_uploader("Upload Documents", type=["txt", "pdf", "csv", "xlsx"], accept_multiple_files=True)
    
    if st.button("Process Documents"):
        if uploaded_files:
            with st.spinner("Extracting & chunking text..."):
                docs = agent_logic.extract_documents(uploaded_files)
                if not docs:
                    st.error("Failed to extract content from the files.")
                else:
                    st.success(f"Extracted document content successfully.")
                    
                    with st.spinner("Building Vector Knowledge Store..."):
                        try:
                            # Storing in session state so it persists across UI interacts
                            st.session_state.vectorstore = agent_logic.build_vector_store(docs, api_key)
                            st.session_state.agent = agent_logic.create_agent(st.session_state.vectorstore, api_key)
                            st.success("Knowledge store ready! You can now start querying.")
                            # Reset chat history for new documents
                            st.session_state.messages = []
                        except Exception as e:
                            st.error(f"Error building vector database: {e}")
        else:
            st.warning("Please upload at least one valid document.")

# Main Chat Interface
st.header("2. AI Agent Query Interface")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if "agent" not in st.session_state:
        with st.chat_message("assistant"):
            st.error("Please process documents first using the sidebar before asking questions.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Agent is reasoning..."):
                try:
                    # Format history for the agent: List of tuples (role, content)
                    formatted_history = [(msg["role"], msg["content"]) for msg in st.session_state.messages[:-1]]
                    formatted_history.append(("user", prompt))
                    
                    response = st.session_state.agent.invoke({
                        "messages": formatted_history
                    })
                    
                    answer = response["messages"][-1].content
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Agent encountered an error: {e}")
