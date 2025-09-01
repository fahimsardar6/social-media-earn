import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from moviepy.editor import ImageClip, AudioFileClip
from dotenv import load_dotenv
import uuid

# Load environment variables locally (optional)
load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

app = FastAPI(title="News Video Generator")

# Request model
class NewsRequest(BaseModel):
    title: str = None
    content: str = None
    image_url: str = None

# Endpoint to generate video
@app.post("/generate-video")
def generate_video(request: NewsRequest):
    # Use default values if not provided
    content = request.content or request.title or "No content provided"
    image_url = request.image_url or "https://via.placeholder.com/720x480.png?text=News"

    # Generate speech via ElevenLabs
    tts_url = "https://api.elevenlabs.io/v1/text-to-speech/alloy"
    tts_headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    tts_data = {"text": content, "model": "eleven_monolingual_v1"}
    tts_response = requests.post(tts_url, json=tts_data)
    if tts_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to generate speech")
    
    audio_file = f"audio_{uuid.uuid4().hex}.mp3"
    with open(audio_file, "wb") as f:
        f.write(tts_response.content)

    # Download image
    img_file = f"image_{uuid.uuid4().hex}.jpg"
    img_response = requests.get(image_url)
    with open(img_file, "wb") as f:
        f.write(img_response.content)

    # Combine image + audio into video
    audio_clip = AudioFileClip(audio_file)
    image_clip = ImageClip(img_file).set_duration(audio_clip.duration)
    image_clip = image_clip.resize(height=720)
    video_file = f"video_{uuid.uuid4().hex}.mp4"
    video_clip = image_clip.set_audio(audio_clip)
    video_clip.write_videofile(video_file, fps=24, codec="libx264", audio_codec="aac")

    return {"video_file": video_file, "message": "Video generated successfully!"}
