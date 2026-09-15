import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the DocAnalyzer project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Synchronize API keys for both Google GenAI and LangChain
gemini_key = os.getenv("GEMINI_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

if gemini_key and not google_key:
    os.environ["GOOGLE_API_KEY"] = gemini_key
elif google_key and not gemini_key:
    os.environ["GEMINI_API_KEY"] = google_key

# Settings
DOCUMENTS_DIR = BASE_DIR / os.getenv("DOCUMENTS_DIR", "documents")
VECTOR_DB_DIR = BASE_DIR / os.getenv("VECTOR_DB_DIR", "data/faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
FALLBACK_LLM_MODEL = os.getenv("FALLBACK_LLM_MODEL", "gemini-3.6-flash")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K = int(os.getenv("TOP_K", "8"))

# Company Website URLs for Ingestion
DEFAULT_COMPANY_URLS = [
    "https://technoindustries.co.in/",
    "https://technoindustries.co.in/about-us/",
    "https://technoindustries.co.in/about-us/from-the-desk-of-management/",
    "https://technoindustries.co.in/key-people/",
    "https://technoindustries.co.in/future-vista/",
    "https://technoindustries.co.in/infrastructure/",
    "https://technoindustries.co.in/institutional-aprovals/",
    "https://technoindustries.co.in/motors/",
    "https://technoindustries.co.in/lt-motors/",
    "https://technoindustries.co.in/blogs/motors/high-tension-ht-motor/",
    "https://technoindustries.co.in/pumps/",
    "https://technoindustries.co.in/contact/",
    "https://technoindustries.co.in/careers/",
    "https://lloydsengg.in/",
]

# Server Settings
STATIC_DIR = BASE_DIR / "static"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
