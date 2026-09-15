import os

# ==========================================
# BASE PATHS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
VIDEO_DIR = os.path.join(BASE_DIR, 'video')
IMAGE_DIR = os.path.join(BASE_DIR, 'images')
THUMBNAIL_DIR = os.path.join(BASE_DIR, 'thumbnails')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
HISTORY_DIR = os.path.join(BASE_DIR, 'history')

# Ensure required directories exist
for d in [AUDIO_DIR, VIDEO_DIR, IMAGE_DIR, THUMBNAIL_DIR, LOG_DIR, HISTORY_DIR]:
    os.makedirs(d, exist_ok=True)

# ==========================================
# CREDENTIALS & AUTH
# ==========================================
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

# ==========================================
# HISTORY & TRACKING FILES
# ==========================================
UPLOADS_HISTORY_FILE = os.path.join(HISTORY_DIR, 'uploads.json')
IMAGES_HISTORY_FILE = os.path.join(HISTORY_DIR, 'images_used.json')
SCRIPTS_HISTORY_FILE = os.path.join(HISTORY_DIR, 'scripts_used.json')
TOPIC_HISTORY_FILE = os.path.join(HISTORY_DIR, 'topic_history.json')
LOG_FILE = os.path.join(LOG_DIR, 'automation.log')
LAST_RUN_FILE = os.path.join(LOG_DIR, 'last_run.txt')

# ==========================================
# TOPICS & SCHEDULE (2 VIDEOS PER DAY)
# ==========================================
TOPICS = ['moral_story', 'animal_story', 'good_habits', 'abc', 'numbers']

# Schedule slots for the 2 daily videos
SCHEDULE_SLOTS = {
    'morning': '09:00',
    'evening': '21:30'
}

# ==========================================
# TTS / VOICE SETTINGS
# ==========================================
VOICE_NAME = 'hi-IN-SwaraNeural'  # Clear, pleasant Hindi voice
VOICE_RATE = '+0%'

# ==========================================
# VIDEO & THUMBNAIL SETTINGS
# ==========================================
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 25
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# Subtitle styling for FFmpeg
SUBTITLE_STYLE = (
    'FontSize=26,'
    'PrimaryColour=&H0000FFFF,'  # Bright yellow
    'OutlineColour=&H00000000,'  # Black border
    'BackColour=&H80000000,'     # Soft semi-transparent background
    'BorderStyle=1,'
    'Outline=2,'
    'Shadow=1,'
    'Alignment=2,'              # Bottom center
    'MarginV=36,'
    'Bold=1'
)

# ==========================================
# YOUTUBE METADATA & COMPLIANCE
# ==========================================
CHANNEL_NAME = 'Fun Learning Kids'
YOUTUBE_CATEGORY_ID = '27'        # Education
YOUTUBE_MADE_FOR_KIDS = True      # Mandatory for COPPA on kids channels
DEFAULT_PRIVACY_STATUS = 'public' # Can be set to 'unlisted' for dry-runs
