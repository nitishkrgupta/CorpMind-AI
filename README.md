# 🏢 DocAnalyzer AI — Enterprise Document & Website Chatbot

A high-performance, production-ready AI Chatbot and RAG (Retrieval-Augmented Generation) system designed to engage website visitors, answer customer product inquiries, and assist employees with corporate policies.

Featuring a **dual-domain knowledge base**, a **FastAPI backend**, an **embeddable floating web widget** with drag-to-resize controls, and a **full-page interactive UI**.

---

## ✨ Key Features

- **🌐 Dual-Domain RAG Architecture**:
  - **Live Website Ingestion**: Scrapes product catalogs, HT/LT induction motors, pumps, certifications, and infrastructure directly from corporate website URLs.
  - **Internal Policy Ingestion**: Processes multi-page PDF documents (Attendance, Leave rules, Travel allowances).
- **💬 Embeddable Floating Chat Widget (`widget.js`)**:
  - Drop onto **any website** (WordPress, HTML, React, etc.) with a single `<script>` tag.
  - **Interactive Drag-to-Resize**: Drag the top-left corner or edges to expand or shrink the chat window to any custom size.
  - **One-Click Maximize / Restore**: Quick expand toggle for comfortable reading.
  - **Structured Markdown**: Renders clean headings, bold text, bulleted lists, and clickable source citations.
- **⚡ In-Memory Pre-Warming**: Pre-loads embeddings and FAISS index into RAM on startup, delivering responses in under 1 second.
- **🧠 Multi-Turn Conversational Memory**: Remembers context across questions and reformulates follow-up queries with pronoun resolution.
- **🛡️ Rate-Limit Resilient**: Quota-optimized routing using `gemini-3.5-flash-lite` with automatic fallback to `gemini-3.6-flash`.
- **☁️ Cloud & Render Ready**: Includes `render.yaml` Blueprint and `runtime.txt` for one-click deployment on Render.

---

## 📁 Project Structure

```
DocAnalyzer/
├── app.py                     # Application server entrypoint (FastAPI + Uvicorn)
├── render.yaml                # Render Infrastructure-as-Code Blueprint
├── runtime.txt                # Python runtime specification (3.11.9)
├── requirements.txt           # Production dependencies
├── .env.example               # Template for environment variables
├── .gitignore                 # Git ignore configuration
├── src/
│   ├── api.py                 # FastAPI REST API endpoints (/api/chat, /api/health)
│   ├── config.py              # Centralized configuration & environment loader
│   ├── ingest.py              # Web crawler + PDF document chunker & FAISS builder
│   ├── memory.py              # SessionManager for multi-turn conversations
│   └── rag.py                 # Dual-domain RAG engine, query rephrasing & LLM routing
├── static/
│   ├── index.html             # Full-page responsive chat dashboard (with Wide View toggle)
│   ├── widget.js              # Embeddable, resizable floating chatbot widget
│   └── demo.html              # Corporate portal mockup demonstrating widget integration
├── data/
│   └── faiss_index/           # Persistent vector database (index.faiss, index.pkl)
└── documents/                 # Corporate policy PDFs
```

---

## 🚀 Local Quickstart

### 1. Clone & Setup Environment
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```ini
GEMINI_API_KEY=your_google_gemini_api_key_here
LLM_MODEL=gemini-3.5-flash-lite
FALLBACK_LLM_MODEL=gemini-3.6-flash
PORT=8000
```

### 3. Run Knowledge Ingestion (Optional)
If you want to re-scrape the website or add new PDF documents to `documents/`:
```bash
python -m src.ingest
```

### 4. Start the Application
```bash
python app.py
```
- **Full Chat UI**: http://localhost:8000
- **Widget Demo**: http://localhost:8000/static/demo.html
- **Interactive Swagger Docs**: http://localhost:8000/docs

---

## 🌐 Deploying to Render (Step-by-Step)

### Option A: 1-Click Blueprint Deployment (Recommended)
1. Push this repository to **GitHub**.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Select your GitHub repository.
5. Render will automatically detect `render.yaml`.
6. Enter your `GEMINI_API_KEY` under Environment Variables.
7. Click **Apply**. Render will automatically build and deploy!

### Option B: Manual Web Service Setup
1. On Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the following settings:
   - **Name**: `docanalyzer-ai` (or your chosen name)
   - **Region**: Oregon (or your preferred region)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION` = `3.11.9`
   - `GEMINI_API_KEY` = *(Your Google Gemini API Key from AI Studio)*
   - `LLM_MODEL` = `gemini-3.5-flash-lite`
   - `FALLBACK_LLM_MODEL` = `gemini-3.6-flash`
5. Click **Deploy Web Service**.

---

## 🔌 Embedding the Chatbot on Your Website

Once deployed on Render (e.g. `https://docanalyzer-ai.onrender.com`), add this snippet right before `</body>` on any webpage:

```html
<script 
  src="https://docanalyzer-ai.onrender.com/static/widget.js" 
  data-api-url="https://docanalyzer-ai.onrender.com"
  data-title="Company Assistant"
  data-greeting="Hello! Welcome to Techno Industries. How can I assist you today?">
</script>
```

---

## 📡 API Reference

### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "DocAnalyzer RAG API"
}
```

### Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What kind of electric motors do you manufacture?",
  "session_id": "optional-uuid"
}
```

**Response:**
```json
{
  "answer": "We manufacture HT (High Tension) and LT (Low Tension) induction motors...",
  "sources": [
    {
      "source": "https://technoindustries.co.in/lt-motors/",
      "page": "N/A",
      "snippet": "..."
    }
  ],
  "session_id": "9f32e18d-4b8c-4a11-a8e7-142c3d52671a"
}
```
