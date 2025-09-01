import requests
from moviepy.editor import ImageClip, AudioFileClip

# -------------------------------
# CONFIGURATION
# -------------------------------
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Example: fetch one top headline
NEWSAPI_URL = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=1&apiKey={NEWSAPI_KEY}"

# Output filenames
AUDIO_FILE = "speech.mp3"
VIDEO_FILE = "news_video.mp4"

# -------------------------------
# 1. Fetch news from NewsAPI
# -------------------------------
response = requests.get(NEWSAPI_URL).json()
article = response['articles'][0]

title = article['title']
content = article['description'] or article['content'] or title
image_url = article['urlToImage']

print(f"Title: {title}")
print(f"Content: {content}")
print(f"Image: {image_url}")

# -------------------------------
# 2. Generate speech using ElevenLabs
# -------------------------------
tts_url = "https://api.elevenlabs.io/v1/text-to-speech/YOUR_VOICE_ID"  # Replace with your voice ID
tts_headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}
tts_data = {
    "text": content,
    "voice": "alloy",   # or your chosen voice
    "model": "eleven_monolingual_v1"
}

tts_response = requests.post(tts_url, json=tts_data)
with open(AUDIO_FILE, "wb") as f:
    f.write(tts_response.content)

# -------------------------------
# 3. Download news image
# -------------------------------
img_response = requests.get(image_url)
img_file = "news_image.jpg"
with open(img_file, "wb") as f:
    f.write(img_response.content)

# -------------------------------
# 4. Combine image + audio to video
# -------------------------------
audio_clip = AudioFileClip(AUDIO_FILE)
image_clip = ImageClip(img_file).set_duration(audio_clip.duration)

# Optional: resize image
image_clip = image_clip.resize(height=720)  # keeps aspect ratio

video_clip = image_clip.set_audio(audio_clip)
video_clip.write_videofile(VIDEO_FILE, fps=24)

print("Video generated successfully!")
