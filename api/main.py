from fastapi import FastAPI
from api.generate_video import app
import uvicorn
import webbrowser
from threading import Timer

def open_browser():
    webbrowser.open("http://127.0.0.1:8000/generate-video")

if __name__ == "__main__":
    try:
        # Open browser after a short delay to ensure server is running
        Timer(1.5, open_browser).start()
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        print(f"Error starting server: {e}")
        raise
