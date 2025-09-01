import os
import requests
from fastapi import FastAPI, Request, HTTPException
from moviepy.editor import ImageClip, AudioFileClip
import uuid
from dotenv import load_dotenv

# Load .env locally
load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

app = FastAPI(title="News Video Generator")

VIDEO_FOLDER = "/tmp"

def unique_filename(prefix, ext):
    return f"{VIDEO_FOLDER}/{prefix}_{uuid.uuid4().hex}.{ext}"

@app.post("/generate-video")
async def generate_video(request: Request):
    data = await request.json()
    content = data.get("content") or data.get("title") or "No content provided"
    image_url = data.get("image_url") or "https://via.placeholder.com/720x480.png?text=News"

    # 1️⃣ Generate audio via ElevenLabs
    tts_url = "https://api.elevenlabs.io/v1/text-to-speech/alloy"
    tts_headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    tts_data = {"text": content, "model": "eleven_monolingual_v1"}
    tts_response = requests.post(tts_url, json=tts_data)
    if tts_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to generate speech")

    audio_file = unique_filename("audio", "mp3")
    with open(audio_file, "wb") as f:
        f.write(tts_response.content)

    # 2️⃣ Download image
    img_file = unique_filename("image", "jpg")
    img_response = requests.get(image_url)
    with open(img_file, "wb") as f:
        f.write(img_response.content)

    # 3️⃣ Combine image + audio into video
    audio_clip = AudioFileClip(audio_file)
    image_clip = ImageClip(img_file).set_duration(audio_clip.duration).resize(height=720)
    video_file = unique_filename("video", "mp4")
    video_clip = image_clip.set_audio(audio_clip)
    video_clip.write_videofile(video_file, fps=24, codec="libx264", audio_codec="aac")

    # 4️⃣ Return local file path (Vercel serverless cannot make it publicly accessible)
    return {"video_file_path": video_file, "message": "Video generated successfully!"}
