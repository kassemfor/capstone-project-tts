import os
import pandas as pd
from PyPDF2 import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.tools import create_retriever_tool
from langgraph.prebuilt import create_react_agent
from langchain_core.documents import Document

def extract_documents(uploaded_files):
    """Extract text from uploaded files (PDF, TXT, CSV, Excel)."""
    docs = []
    for file in uploaded_files:
        content = ""
        filename = file.name
        try:
            if filename.endswith('.txt'):
                content = file.read().decode('utf-8')
            elif filename.endswith('.pdf'):
                pdf = PdfReader(file)
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
            elif filename.endswith('.csv'):
                df = pd.read_csv(file)
                content = df.to_string()
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(file)
                content = df.to_string()
                
            if content.strip():
                docs.append(Document(page_content=content, metadata={"source": filename}))
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    return docs

def build_vector_store(docs, api_key):
    """Chunk documents, embed them, and store in a Chroma vector database."""
    # Split documents into meaningful chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    # Create Google GenAI embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=api_key)
    
    # Create Chroma vector store in memory
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    return vectorstore

def create_agent(vectorstore, api_key):
    """Create a LangChain Tool-calling agent with access to the document vector store."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Tool for the agent to search the uploaded documents
    retriever_tool = create_retriever_tool(
        retriever,
        "document_search_tool",
        "Search for information in the user's uploaded documents (PDFs, TXTs, CSVs, Excel). Always use this tool when answering questions about the uploaded content."
    )
    
    tools = [retriever_tool]
    
    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.2)
    
    system_message = (
        "You are an intelligent organizational agent designed to help users query their enterprise documents. "
        "You must use the provided document_search_tool to retrieve relevant context to answer the questions. "
        "If you do not know the answer based on the context, politely state that the information is not in the documents. "
        "Avoid hallucinations and prioritize safety and accuracy. "
        "Think step-by-step and provide grounded responses."
    )
    
    # Construct the tool calling agent using LangGraph
    agent = create_react_agent(llm, tools, prompt=system_message)
    
    return agent
