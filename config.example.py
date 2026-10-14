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
# Place your Google Cloud OAuth 2.0 Client Secret file here
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
# Generated automatically upon first interactive run via auth_setup.py
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

# Upload and management scopes (required for daily video uploads)
UPLOAD_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

# Read-only Analytics scope (for channel and video performance metrics)
ANALYTICS_SCOPES = [
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]

# All scopes combined (used during interactive auth_setup.py)
SCOPES = UPLOAD_SCOPES + ANALYTICS_SCOPES

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
# TOPICS & SCHEDULE (2 NORMAL VIDEOS PER DAY)
# ==========================================
TOPICS = ['moral_story', 'animal_story', 'good_habits', 'abc', 'numbers']

# Schedule slots for the normal daily videos
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
# DUAL FORMAT PROFILES (LANDSCAPE & SHORTS)
# ==========================================
FORMAT_LANDSCAPE = 'landscape'
FORMAT_SHORTS = 'shorts'
DEFAULT_FORMAT = FORMAT_LANDSCAPE

FORMAT_PROFILES = {
    FORMAT_LANDSCAPE: {
        'name': 'landscape',
        'width': 1280,
        'height': 720,
        'aspect_ratio': '16:9',
        'fps': 25,
        'thumbnail_width': 1280,
        'thumbnail_height': 720,
        'subtitle_style': (
            'FontSize=26,'
            'PrimaryColour=&H0000FFFF,'
            'OutlineColour=&H00000000,'
            'BackColour=&H80000000,'
            'BorderStyle=1,'
            'Outline=2,'
            'Shadow=1,'
            'Alignment=2,'
            'MarginV=36,'
            'Bold=1'
        ),
        'tag_shorts': False
    },
    FORMAT_SHORTS: {
        'name': 'shorts',
        'width': 1080,
        'height': 1920,
        'aspect_ratio': '9:16',
        'fps': 25,
        'thumbnail_width': 1080,
        'thumbnail_height': 1920,
        'subtitle_style': (
            'FontSize=44,'
            'PrimaryColour=&H0000FFFF,'
            'OutlineColour=&H00000000,'
            'BackColour=&H80000000,'
            'BorderStyle=1,'
            'Outline=3,'
            'Shadow=2,'
            'Alignment=2,'
            'MarginV=260,'
            'Bold=1'
        ),
        'tag_shorts': True
    }
}

# Daily format split (Slot 1 = Shorts, Slot 2 = Landscape, Slot 3 = Cartoon)
DAILY_SLOT_FORMATS = {
    'morning': FORMAT_SHORTS,
    'evening': FORMAT_LANDSCAPE,
    'cartoon': FORMAT_LANDSCAPE
}

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 25
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# ==========================================
# YOUTUBE METADATA & COMPLIANCE
# ==========================================
CHANNEL_NAME = 'Fun Learning Kids'
YOUTUBE_CATEGORY_ID = '27'        # Education
YOUTUBE_MADE_FOR_KIDS = True      # Mandatory for COPPA on kids channels
DEFAULT_PRIVACY_STATUS = 'public' # Can be set to 'unlisted' for dry-runs
