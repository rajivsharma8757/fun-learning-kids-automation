import os

CARTOON_DIR = r'C:\kids_automation\cartoon'
ASSETS_DIR = os.path.join(CARTOON_DIR, 'assets')
CHARACTERS_DIR = os.path.join(ASSETS_DIR, 'characters')
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, 'backgrounds')
PROPS_DIR = os.path.join(ASSETS_DIR, 'props')
AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
OUTPUT_DIR = os.path.join(CARTOON_DIR, 'output')
THUMBNAILS_DIR = os.path.join(CARTOON_DIR, 'thumbnails')

HISTORY_DIR = r'C:\kids_automation\history'
CARTOON_HISTORY_FILE = os.path.join(HISTORY_DIR, 'cartoon_history.json')

# Video Specifications
WIDTH = 1280
HEIGHT = 720
FPS = 30
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'
AUDIO_SAMPLE_RATE = 48000

# Audio Mixing Settings
MUSIC_VOLUME = 0.12     # -18.4 dB relative to dialogue for clear comprehension
SFX_VOLUME = 0.25       # Subtle action cues

# Voice Configuration
VOICE_NARRATOR = 'hi-IN-SwaraNeural'
VOICE_MALE_CHAR = 'hi-IN-MadhurNeural'

CHANNEL_NAME = 'Fun Learning Kids'