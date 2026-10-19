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
BRANDING_DIR = os.path.join(BASE_DIR, 'branding')
MIGRATION_DIR = os.path.join(BASE_DIR, 'migration')

# Ensure required directories exist
for d in [AUDIO_DIR, VIDEO_DIR, IMAGE_DIR, THUMBNAIL_DIR, LOG_DIR, HISTORY_DIR, BRANDING_DIR, MIGRATION_DIR]:
    os.makedirs(d, exist_ok=True)

# ==========================================
# CHANNEL PROFILES & TWO-LAYER SAFEGUARDS
# ==========================================
PROFILE_NANHE_SEEKHO = "nanhe_seekho_club"
PROFILE_FUN_LEARNING = "fun_learning_kids"

# Legacy channel ID that is STRICTLY PROTECTED from any new uploads or modifications
LEGACY_PROTECTED_CHANNEL_ID = "UCcOA6heUaTbOUnx7ERF23Gw"
ALLOW_LEGACY_CHANNEL_UPLOADS = False

CHANNEL_PROFILES = {
    PROFILE_NANHE_SEEKHO: {
        "channel_id": None,  # Dynamically verified via YouTube API upon authorization
        "name": "Nanhe Seekho Club",
        "name_hi": "नन्हे सीखो क्लब",
        "tagline_en": "Little Minds, Big Discoveries!",
        "tagline_hi": "छोटे कदम, बड़ी खोज!",
        "handle": "@NanheSeekhoClub",
        "token_file": os.path.join(BASE_DIR, "token_nanhe_seekho_club.json"),
        "uploads_history_file": os.path.join(HISTORY_DIR, "uploads_nanhe_seekho_club.json"),
        "images_history_file": os.path.join(HISTORY_DIR, "images_used_nanhe_seekho_club.json"),
        "scripts_history_file": os.path.join(HISTORY_DIR, "scripts_used_nanhe_seekho_club.json"),
        "topic_history_file": os.path.join(HISTORY_DIR, "topic_history_nanhe_seekho_club.json"),
        "cartoon_history_file": os.path.join(HISTORY_DIR, "cartoon_history_nanhe_seekho_club.json"),
        "daily_jobs_file": os.path.join(HISTORY_DIR, "daily_job_states_nanhe_seekho_club.json"),
        "last_run_file": os.path.join(LOG_DIR, "last_run_nanhe_seekho_club.txt"),
        "schedule": {
            "daily_shorts": True,
            "daily_shorts_time": "09:00",
            "long_videos_per_week": 2,
            "long_video_days": [2, 6],  # Wednesday (2) and Sunday (6)
            "long_video_time": "17:00"
        },
        "is_active": True,
        "is_protected": False
    },
    PROFILE_FUN_LEARNING: {
        "channel_id": LEGACY_PROTECTED_CHANNEL_ID,
        "name": "Fun Learning Kids",
        "name_hi": "फन लर्निंग किड्स",
        "tagline_en": "Fun Learning for Kids",
        "tagline_hi": "बच्चों के लिए मजेदार सीख",
        "handle": "@FunLearningKids",
        "token_file": os.path.join(BASE_DIR, "token.json"),
        "uploads_history_file": os.path.join(HISTORY_DIR, "uploads.json"),
        "images_history_file": os.path.join(HISTORY_DIR, "images_used.json"),
        "scripts_history_file": os.path.join(HISTORY_DIR, "scripts_used.json"),
        "topic_history_file": os.path.join(HISTORY_DIR, "topic_history.json"),
        "cartoon_history_file": os.path.join(HISTORY_DIR, "cartoon_history.json"),
        "daily_jobs_file": os.path.join(HISTORY_DIR, "daily_job_states.json"),
        "last_run_file": os.path.join(LOG_DIR, "last_run.txt"),
        "schedule": {
            "daily_shorts": True,
            "daily_shorts_time": "09:00",
            "evening_time": "21:30"
        },
        "is_active": False,
        "is_protected": True  # Uploads strictly blocked by code
    }
}

ACTIVE_PROFILE_NAME = os.getenv("CHANNEL_PROFILE", PROFILE_NANHE_SEEKHO).lower()
if ACTIVE_PROFILE_NAME not in CHANNEL_PROFILES:
    ACTIVE_PROFILE_NAME = PROFILE_NANHE_SEEKHO

ACTIVE_PROFILE = CHANNEL_PROFILES[ACTIVE_PROFILE_NAME]

# ==========================================
# CREDENTIALS & AUTH
# ==========================================
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = ACTIVE_PROFILE["token_file"]

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
# HISTORY & TRACKING FILES (ACTIVE PROFILE)
# ==========================================
UPLOADS_HISTORY_FILE = ACTIVE_PROFILE["uploads_history_file"]
IMAGES_HISTORY_FILE = ACTIVE_PROFILE["images_history_file"]
SCRIPTS_HISTORY_FILE = ACTIVE_PROFILE["scripts_history_file"]
TOPIC_HISTORY_FILE = ACTIVE_PROFILE["topic_history_file"]
CARTOON_HISTORY_FILE = ACTIVE_PROFILE["cartoon_history_file"]
DAILY_JOBS_FILE = ACTIVE_PROFILE["daily_jobs_file"]
LAST_RUN_FILE = ACTIVE_PROFILE["last_run_file"]

LOG_FILE = os.path.join(LOG_DIR, 'automation.log')

# ==========================================
# TOPICS & SCHEDULE CONFIGURATION
# ==========================================
TOPICS = ['moral_story', 'animal_story', 'good_habits', 'abc', 'numbers']

SCHEDULE_SLOTS = {
    'morning': '09:00',
    'evening': '17:00',
    'shorts': '09:00',
    'long_video': '17:00'
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
            'PrimaryColour=&H0000FFFF,'  # Bright yellow
            'OutlineColour=&H00000000,'  # Black border
            'BackColour=&H80000000,'     # Soft semi-transparent background
            'BorderStyle=1,'
            'Outline=2,'
            'Shadow=1,'
            'Alignment=2,'              # Bottom center
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
            'PrimaryColour=&H0000FFFF,'  # Bright yellow
            'OutlineColour=&H00000000,'  # Black border
            'BackColour=&H80000000,'     # Soft semi-transparent background
            'BorderStyle=1,'
            'Outline=3,'
            'Shadow=2,'
            'Alignment=2,'              # Bottom center
            'MarginV=260,'             # Safe zone above Shorts UI overlay
            'Bold=1'
        ),
        'tag_shorts': True
    }
}

# Environment override or default landscape
VIDEO_FORMAT = os.getenv("VIDEO_FORMAT", DEFAULT_FORMAT).lower()
_active_profile = FORMAT_PROFILES.get(VIDEO_FORMAT, FORMAT_PROFILES[DEFAULT_FORMAT])

# Balanced slot format allocation
DAILY_SLOT_FORMATS = {
    'morning': FORMAT_SHORTS,
    'shorts': FORMAT_SHORTS,
    'evening': FORMAT_LANDSCAPE,
    'cartoon': FORMAT_LANDSCAPE,
    'long_video': FORMAT_LANDSCAPE
}

# Backwards-compatible globals
VIDEO_WIDTH = _active_profile['width']
VIDEO_HEIGHT = _active_profile['height']
VIDEO_FPS = _active_profile['fps']
THUMBNAIL_WIDTH = _active_profile['thumbnail_width']
THUMBNAIL_HEIGHT = _active_profile['thumbnail_height']
SUBTITLE_STYLE = _active_profile['subtitle_style']

# ==========================================
# YOUTUBE METADATA & COMPLIANCE
# ==========================================
CHANNEL_NAME = ACTIVE_PROFILE['name']
CHANNEL_NAME_HI = ACTIVE_PROFILE['name_hi']
CHANNEL_TAGLINE_EN = ACTIVE_PROFILE['tagline_en']
CHANNEL_TAGLINE_HI = ACTIVE_PROFILE['tagline_hi']
CHANNEL_HANDLE = ACTIVE_PROFILE['handle']

YOUTUBE_CATEGORY_ID = '27'        # Education
YOUTUBE_MADE_FOR_KIDS = True      # Mandatory for COPPA on kids channels
DEFAULT_PRIVACY_STATUS = 'public' # Can be set to 'unlisted' for dry-runs
