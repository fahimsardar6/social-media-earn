import sys
if sys.version_info >= (3, 12):
    print("Warning: This application works best with Python 3.10 or 3.11")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
from functools import partial
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from moviepy.config import change_settings
from newspaper import Article
from newsapi import NewsApiClient
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from dotenv import load_dotenv
import os
import uuid

# Load environment variables
load_dotenv()

# Optional BERT import
try:
    from summarizer import Summarizer
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    print("Warning: BERT summarizer not available. Full text will be used.")

app = FastAPI()

# 🔑 Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Init API clients
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Configure MoviePy to use ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

# Initialize summarizer only if available
model = Summarizer() if BERT_AVAILABLE else None


def generate_elevenlabs_voice(text, filename):
    """Generate voice using ElevenLabs SDK and save as MP3"""
    try:
        response = eleven_client.text_to_speech.convert(
            text=text,
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
            model_id="eleven_monolingual_v1",
            output_format="mp3_22050_32",
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
                speed=1.0,
            ),
        )
        
        with open(filename, "wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)
        return filename
    except Exception as e:
        raise Exception(f"ElevenLabs conversion failed: {str(e)}")


class VideoResponse(BaseModel):
    message: str
    video_title: str
    video_file: str
    article_url: str
    content_type: str
    content_length: int


@app.get("/")
async def status():
    return {"status": "API is running", "endpoints": ["/generate-video"]}


def run_in_executor(func, *args):
    """Run blocking functions in executor"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args)

@app.get("/generate-video", response_model=VideoResponse)
async def generate_video(short: bool = False):
    # Initialize resources to None
    video = None
    narration = None
    txt_clip = None
    final_video = None
    audio_filename = None
    output_filename = None

    try:
        # ✅ Step 1: Get latest BBC News headline
        headlines = newsapi.get_top_headlines(sources="bbc-news", language="en", page_size=1)

        if not headlines["articles"]:
            raise HTTPException(status_code=404, detail="No news articles found")

        article = headlines["articles"][0]
        title = article["title"]
        article_url = article["url"]

        # ✅ Step 2: Extract full article
        news_article = Article(article_url)
        news_article.download()
        news_article.parse()
        content_full = news_article.text.strip()

        if not content_full:
            raise HTTPException(status_code=404, detail="No content extracted from article")

        # ✅ Step 3: Summarize or keep full
        if short and BERT_AVAILABLE and model:
            content = model(content_full, min_length=40, max_length=100)
        else:
            content = content_full

        # ✅ Step 4: Generate narration
        audio_filename = f"temp/audio_{uuid.uuid4().hex}.mp3"
        os.makedirs("temp", exist_ok=True)
        generate_elevenlabs_voice(content, audio_filename)

        # ✅ Step 5: Combine with static video
        static_video_path = "static/static_background.mp4"
        if not os.path.exists(static_video_path):
            raise HTTPException(status_code=404, detail=f"Static video not found: {static_video_path}")

        # Load and resize video for mobile (9:16 aspect ratio)
        video = VideoFileClip(static_video_path).resize(newsize=(1080, 1920))
        narration = AudioFileClip(audio_filename)

        # Loop video if narration is longer
        if narration.duration > video.duration:
            loops_needed = int(narration.duration / video.duration) + 1
            video_loops = [video] * loops_needed
            final_video = concatenate_videoclips(video_loops).subclip(0, narration.duration)
        else:
            final_video = video.subclip(0, narration.duration)

        # Add caption with font size and position adjusted for vertical video
        txt_clip = (TextClip(title, 
                             fontsize=50, 
                             color='white',
                             bg_color='rgba(0,0,0,0.5)',
                             size=final_video.size, 
                             method='caption',
                             stroke_color='black',
                             stroke_width=2)
                     .set_position(('center', 'bottom'))
                     .set_duration(final_video.duration))

        # Combine video with caption
        final_video = CompositeVideoClip([final_video, txt_clip])
        final_video = final_video.set_audio(narration)
        
        output_filename = f"output/generated_{uuid.uuid4().hex}.mp4"
        os.makedirs("output", exist_ok=True)
        final_video.write_videofile(output_filename, codec="libx264", audio_codec="aac")

        return {
            "message": "Video generated successfully",
            "video_title": title,
            "video_file": output_filename,
            "article_url": article_url,
            "content_type": "summary" if short else "full",
            "content_length": len(content),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up resources
        try:
            if txt_clip: txt_clip.close()
            if narration: narration.close()
            if video: video.close()
            if final_video: final_video.close()
            if audio_filename and os.path.exists(audio_filename):
                os.remove(audio_filename)
        except Exception as e:
            print(f"Cleanup error: {e}")
