import os
import sys
import time
import random
import logging
import subprocess
from config import VOICE_NAME, VOICE_RATE

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("kids_automation")


def get_audio_duration(audio_path):
    """Returns the duration of the audio file in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Error reading audio duration with ffprobe: {e}")
        return 0.0


def generate_voice(voice_text, output_audio_path, output_vtt_path=None, max_retries=5):
    """
    Generates Hindi voice using edge-tts.
    Handles network dropouts and websocket handshake retries with backoff & jitter.
    Validates output file size and ffprobe duration.
    """
    if os.path.exists(output_audio_path):
        try:
            os.remove(output_audio_path)
        except Exception:
            pass

    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", VOICE_NAME,
        "--text", voice_text,
        "--write-media", output_audio_path
    ]
    if output_vtt_path:
        cmd.extend(["--write-subtitles", output_vtt_path])

    for attempt in range(1, max_retries + 1):
        logger.info(f"🎙️ Generating voice narration (attempt {attempt}/{max_retries})...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=50)
            if res.returncode == 0 and os.path.exists(output_audio_path):
                file_size = os.path.getsize(output_audio_path)
                if file_size > 2000:
                    duration = get_audio_duration(output_audio_path)
                    if duration > 1.0:
                        logger.info(f"✅ Voice generated successfully! ({duration:.2f}s, {file_size:,} bytes)")
                        return True, duration
                    else:
                        logger.warning(f"⚠️ Audio file duration too short ({duration}s).")
                else:
                    logger.warning(f"⚠️ Audio file suspiciously small: {file_size} bytes.")
            else:
                err_msg = res.stderr.strip()[:300]
                logger.warning(f"⚠️ Edge-TTS error on attempt {attempt}: {err_msg}")
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ Edge-TTS command timed out on attempt {attempt} after 50s.")
        except Exception as e:
            logger.warning(f"⚠️ Voice generation exception on attempt {attempt}: {e}")

        if attempt < max_retries:
            wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
            logger.info(f"⏳ Retrying voice generation in {wait_time:.1f}s...")
            time.sleep(wait_time)

    # Clean up corrupt file if failed
    if os.path.exists(output_audio_path):
        try:
            os.remove(output_audio_path)
        except Exception:
            pass

    logger.error("❌ Voice generation failed after all retry attempts.")
    return False, 0.0
