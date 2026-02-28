import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
from gtts import gTTS
import os
from dotenv import load_dotenv
import io
import requests

# Load environment variables
load_dotenv()

def inject_custom_css():
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: radial-gradient(circle at top left, #1a1a2e, #16213e, #0f3460);
        color: #ffffff;
    }

    /* Glass container */
    .glass-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Professional Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Inputs and Selectboxes */
    .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 210, 255, 0.4);
    }

    /* Sidebar info */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Center aligning main content */
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.warning("Please set your GEMINI_API_KEY in the .env file or environment variables.")

# Supported languages in gTTS mapping to Gemini translation instructions
SUPPORTED_LANGUAGES = {
    'af': 'Afrikaans', 'ar': 'Arabic', 'bg': 'Bulgarian', 'bn': 'Bengali', 'bs': 'Bosnian',
    'ca': 'Catalan', 'cs': 'Czech', 'da': 'Danish', 'de': 'German', 'el': 'Greek',
    'en': 'English', 'es': 'Spanish', 'et': 'Estonian', 'fi': 'Finnish', 'fr': 'French',
    'gu': 'Gujarati', 'hi': 'Hindi', 'hr': 'Croatian', 'hu': 'Hungarian', 'id': 'Indonesian',
    'is': 'Icelandic', 'it': 'Italian', 'iw': 'Hebrew', 'ja': 'Japanese', 'jw': 'Javanese',
    'km': 'Khmer', 'kn': 'Kannada', 'ko': 'Korean', 'la': 'Latin', 'lv': 'Latvian',
    'ml': 'Malayalam', 'mr': 'Marathi', 'ms': 'Malay', 'my': 'Myanmar (Burmese)',
    'ne': 'Nepali', 'nl': 'Dutch', 'no': 'Norwegian', 'pl': 'Polish', 'pt': 'Portuguese',
    'ro': 'Romanian', 'ru': 'Russian', 'si': 'Sinhala', 'sk': 'Slovak', 'sq': 'Albanian',
    'sr': 'Serbian', 'su': 'Sundanese', 'sv': 'Swedish', 'sw': 'Swahili', 'ta': 'Tamil',
    'te': 'Telugu', 'th': 'Thai', 'tl': 'Filipino', 'tr': 'Turkish', 'uk': 'Ukrainian',
    'ur': 'Urdu', 'vi': 'Vietnamese', 'zh-CN': 'Chinese (Simplified)', 'zh-TW': 'Chinese (Traditional)'
}

def extract_text_from_file(uploaded_file):
    """Function 2: Extract text from uploaded file(txt, pdf, csv, xlsx)"""
    try:
        if uploaded_file.name.endswith('.txt'):
            data = uploaded_file.read().decode('utf-8')
            return data
        elif uploaded_file.name.endswith('.pdf'):
            pdf_reader = PdfReader(uploaded_file)
            data = ""
            for page in pdf_reader.pages:
                data += page.extract_text()
            return data
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            data = " ".join(df.astype(str).values.flatten())
            return data
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            data = " ".join(df.astype(str).values.flatten())
            return data
        else:
            return ""
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

def translate_text(text, target_language_name, provider="Google Gemini", ollama_model="llama3", local_url=""):
    """Function 1 : Translated to text using Gemini or Local Models"""
    try:
        prompt = f"Translate the following text into {target_language_name}. Provide ONLY the translation, without any conversational text or markdown formatting of the translation itself.\n\nText:\n{text}"
        
        if provider == "Google Gemini":
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text.strip()
            
        elif provider == "Ollama (Local)":
            data = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(local_url, json=data)
            response.raise_for_status()
            return response.json().get("response", "").strip()
            
        elif provider == "Llama.cpp Server (Local)":
            data = {
                "messages": [{"role": "user", "content": prompt}]
            }
            response = requests.post(local_url, json=data)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        return None
    except Exception as e:
        st.error(f"Translation Error: {e}")
        return None

def convert_text_to_speech(text, lang_code):
    """Function 3 : Convert translate text into speech"""
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        # Save to buffer instead of disk for direct download
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        st.error(f"Text-to-Speech Error: {e}")
        return None

def main():
    """Wrapper Web-Application using Streamlit"""
    st.set_page_config(page_title="Translate & Speak", page_icon="🌐", layout="wide")
    inject_custom_css()
    
    # Custom Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🌐 Translate & Speak")
    st.markdown('<p style="font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.8;">Orchestrate your global communication with AI-powered translation and speech synthesis.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Main Glass Container
    with st.container():
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        
        input_method = st.radio("Input Method", ("Enter Text", "Upload File"), horizontal=True)
    
    source_text = ""
    
    st.sidebar.header("LLM Settings")
    llm_provider = st.sidebar.selectbox("Select LLM Provider", ["Google Gemini", "Ollama (Local)", "Llama.cpp Server (Local)"])
    
    ollama_model = ""
    local_url = ""
    
    if llm_provider == "Ollama (Local)":
        ollama_model = st.sidebar.text_input("Ollama Model Name", "llama3")
        local_url = st.sidebar.text_input("Ollama API URL", "http://localhost:11434/api/generate")
    elif llm_provider == "Llama.cpp Server (Local)":
        local_url = st.sidebar.text_input("Llama.cpp API URL", "http://localhost:8080/v1/chat/completions")
    elif llm_provider == "Google Gemini":
        st.sidebar.info("Uses GEMINI_API_KEY from .env")

    if input_method == "Enter Text":
        source_text = st.text_area("Enter text to translate:")
    else:
        uploaded_file = st.file_uploader("Upload a file (.txt, .pdf, .csv, .xlsx)", type=["txt", "pdf", "csv", "xlsx"])
        if uploaded_file is not None:
            source_text = extract_text_from_file(uploaded_file)
            if source_text:
                st.success("File successfully extracted!")
                with st.expander("Show Extracted Text"):
                    st.text(source_text[:1000] + ("..." if len(source_text) > 1000 else ""))
        
        st.markdown("---")

    # Create a nice layout for selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # User selects language name (value is the code)
        lang_options = {name: code for code, name in SUPPORTED_LANGUAGES.items()}
        target_lang_name = st.selectbox("Select Target Language", list(lang_options.keys()))
        target_lang_code = lang_options[target_lang_name]

    if st.button("Translate & Generate Audio", type="primary"):
        if llm_provider == "Google Gemini" and not API_KEY:
            st.error("Cannot proceed with Gemini. GEMINI_API_KEY is not configured.")
            return
            
        if not source_text.strip():
            st.warning("Please enter some text or upload a valid file containing text.")
            return
            
        with st.spinner("Translating text..."):
            translated_text = translate_text(source_text, target_lang_name, llm_provider, ollama_model, local_url)
            
        if translated_text:
            st.success("Translation Complete!")
            st.markdown("### Translated Text:")
            st.write(translated_text)
            
            with st.spinner("Generating audio..."):
                audio_bytes = convert_text_to_speech(translated_text, target_lang_code)
                
            if audio_bytes:
                st.markdown("### Audio generated by gTTS:")
                st.audio(audio_bytes, format="audio/mp3")
                
                st.download_button(
                    label="Download Audio (MP3)",
                    data=audio_bytes,
                    file_name="translated_speech.mp3",
                    mime="audio/mp3"
                )
        
        st.markdown('</div>', unsafe_allow_html=True) # Close glass-container

if __name__ == "__main__":
    main()
