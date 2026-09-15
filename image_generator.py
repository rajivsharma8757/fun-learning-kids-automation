import os
import sys
import time
import random
import hashlib
import io
import urllib.request
import urllib.parse
import logging
from datetime import datetime
from PIL import Image

from config import IMAGE_DIR, BASE_DIR
from notifier import send_notification

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("kids_automation")

TOPIC_BASE_PROMPTS = {
    "moral_story": "wholesome vibrant 2D cartoon storybook illustration for children, cute friendly animals helping each other in a sunny lush forest, bright joyful colors, classic kids storybook art style, high quality, no text",
    "animal_story": "vibrant 2D cartoon storybook illustration of cute playful baby animals in a sunny green meadow with blooming flowers, cheerful and charming kids art style, high quality, no text",
    "good_habits": "cheerful vibrant 2D cartoon illustration of a cute happy child practicing good habits and hygiene, bright cozy room, positive educational preschool storybook art, high quality, no text",
    "abc": "vibrant colorful 2D cartoon educational illustration for preschoolers, cheerful cute animals and nature, bright sunny day, joyful learning storybook art, high quality, no text",
    "numbers": "wholesome vibrant 2D cartoon illustration for toddlers learning numbers and counting, colorful floating balloons, stars, sunny landscape, joyful educational art, high quality, no text"
}

def compute_image_hash(image_bytes):
    """Computes SHA-256 hash of image data."""
    return hashlib.sha256(image_bytes).hexdigest()

def compute_file_hash(filepath):
    """Computes SHA-256 hash of a file on disk."""
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def validate_image(image_bytes, min_size_bytes=15000):
    """
    Validates that image data is not empty, can be read by Pillow,
    and has valid dimensions. Returns PIL Image object if valid, else None.
    """
    if len(image_bytes) < min_size_bytes:
        logger.warning(f"Image data too small: {len(image_bytes)} bytes")
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify() # Verify file integrity
        # Re-open after verify() because verify() empties the buffer
        img = Image.open(io.BytesIO(image_bytes))
        if img.width < 250 or img.height < 200:
            logger.warning(f"Image dimensions too small: {img.size}")
            return None
        return img
    except Exception as e:
        logger.warning(f"Image validation failed: {e}")
        return None

def build_prompt(topic, script=None):
    """Constructs a rich, child-friendly prompt matching the topic and story."""
    base = TOPIC_BASE_PROMPTS.get(topic, TOPIC_BASE_PROMPTS["moral_story"])
    if script:
        title = script.get("short_title") or script.get("title", "")
        # Remove special characters or emoji from prompt
        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "'"))
        if clean_title:
            return f"wholesome vibrant 2D cartoon storybook illustration for children featuring {clean_title}, cute friendly characters, bright cheerful colors, high detail, no text"
    return base

def generate_topic_image(topic, script=None, known_hashes=None, max_attempts=20):
    """
    Generates a new, original child-safe cartoon image for the given topic.
    Implements robust retry logic: minimum 4 attempts, continues retrying beyond 4
    without arbitrary cutoff, using controlled backoff intervals.
    Validates format, checks SHA-256 duplicate protection, and saves to topic folder.
    """
    if known_hashes is None:
        known_hashes = set()

    topic_folder = os.path.join(IMAGE_DIR, topic)
    os.makedirs(topic_folder, exist_ok=True)

    prompt = build_prompt(topic, script)
    logger.info(f"🎨 Starting auto-generation for topic '{topic}'...")
    logger.info(f"   Prompt: {prompt}")

    retry_alert_sent = False
    attempt = 1

    while attempt <= max_attempts:
        logger.info(f"🔄 Image generation attempt {attempt}...")
        seed = random.randint(1000, 9999999)
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FunLearningKids/1.0"}
            )
            # Timeout: 45s per attempt to allow remote image synthesis
            with urllib.request.urlopen(req, timeout=45) as resp:
                if resp.status == 200:
                    data = resp.read()
                    img = validate_image(data)
                    if img:
                        # Ensure 1280x720 16:9 standard resolution
                        if img.size != (1280, 720):
                            img = img.resize((1280, 720), Image.Resampling.LANCZOS)

                        # Encode to JPEG buffer to compute exact file hash
                        buf = io.BytesIO()
                        img.convert("RGB").save(buf, "JPEG", quality=95)
                        final_bytes = buf.getvalue()
                        img_hash = compute_image_hash(final_bytes)

                        if img_hash in known_hashes:
                            logger.warning(f"⚠️ Duplicate image hash detected ({img_hash[:12]}). Retrying fresh seed...")
                        else:
                            # Valid, unique image generated!
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"generated_{timestamp}_{img_hash[:8]}.jpg"
                            target_path = os.path.join(topic_folder, filename)

                            with open(target_path, "wb") as f:
                                f.write(final_bytes)

                            file_size = os.path.getsize(target_path)
                            logger.info(f"✅ New image successfully generated and saved: {filename} ({file_size} bytes)")

                            if retry_alert_sent:
                                send_notification(
                                    "Fun Learning Kids",
                                    "New image generated successfully. Continuing today's video."
                                )

                            return target_path, filename, img_hash
                    else:
                        logger.warning(f"Attempt {attempt}: Downloaded data failed image validation.")
                else:
                    logger.warning(f"Attempt {attempt}: Server returned HTTP {resp.status}")

        except Exception as e:
            logger.warning(f"Attempt {attempt} failed with exception: {e}")

        # Send alert after 3 consecutive failures to inform user without spamming
        if attempt == 3 and not retry_alert_sent:
            send_notification(
                "Fun Learning Kids — Alert",
                "New image generation failed. Retrying automatically..."
            )
            retry_alert_sent = True

        # Controlled backoff intervals:
        # Attempts 1-4: 4s, 6s, 8s, 10s
        # Attempts 5+: 12s, 16s, 20s, up to 30s max
        if attempt < 4:
            delay = 4 + (attempt * 2)
        else:
            delay = min(30, 8 + (attempt - 3) * 4)

        logger.info(f"⏳ Waiting {delay}s before retry attempt {attempt + 1}...")
        time.sleep(delay)
        attempt += 1

    # If all attempts exhausted without recovery
    logger.error("❌ Image generation exhausted all attempts without producing a valid image.")
    send_notification(
        "Fun Learning Kids — Error",
        "Unable to generate required image. Please check the error log."
    )
    return None, None, None

if __name__ == "__main__":
    t = "moral_story"
    res_path, res_fn, res_h = generate_topic_image(t, {"short_title": "The Honest Woodcutter"})
    print("Result Path:", res_path)
    print("Result Filename:", res_fn)
    print("Result Hash:", res_h)
