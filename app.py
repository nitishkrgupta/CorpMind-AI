import uvicorn
from src.config import HOST, PORT

if __name__ == "__main__":
    print(f"[*] Starting DocAnalyzer server on http://{HOST}:{PORT}")
    print(f"[*] Full Web UI: http://localhost:{PORT}")
    print(f"[*] Embed Widget Demo: http://localhost:{PORT}/static/demo.html")
    print(f"[*] API Docs: http://localhost:{PORT}/docs")
    uvicorn.run("src.api:app", host=HOST, port=PORT, reload=False)
