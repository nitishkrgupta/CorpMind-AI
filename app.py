import uvicorn
from src.config import HOST, PORT

if __name__ == "__main__":
    print(f"[*] Starting Tech Industries Assistant on http://{HOST}:{PORT}")
    print(f"[*] Corporate Demo Portal (with Chat Widget): http://localhost:{PORT}")
    print(f"[*] Full-Screen Chat Dashboard: http://localhost:{PORT}/chat")
    print(f"[*] Interactive API Docs: http://localhost:{PORT}/docs")
    uvicorn.run("src.api:app", host=HOST, port=PORT, reload=False)
