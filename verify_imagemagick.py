import os
from moviepy.config import get_setting
from moviepy.video.VideoClip import TextClip
import subprocess

def verify_imagemagick():
    print("Checking ImageMagick installation...")
    
    # 1. Check MoviePy's ImageMagick setting
    imagemagick_path = get_setting("IMAGEMAGICK_BINARY")
    print(f"Current ImageMagick path: {imagemagick_path}")
    
    # 2. Check if file exists
    if os.path.exists(imagemagick_path):
        print("✅ ImageMagick binary found at configured path")
    else:
        print("❌ ImageMagick binary NOT found at configured path")
        
    # 3. Try to run ImageMagick
    try:
        result = subprocess.run([imagemagick_path, "-version"], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✅ ImageMagick is working correctly")
            print(f"Version info:\n{result.stdout.split('\\n')[0]}")
        else:
            print("❌ Error running ImageMagick")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    # 4. Test text rendering
    try:
        clip = TextClip("Test", fontsize=30)
        clip.close()
        print("✅ TextClip creation successful")
    except Exception as e:
        print(f"❌ Error creating TextClip: {str(e)}")

if __name__ == "__main__":
    verify_imagemagick()
