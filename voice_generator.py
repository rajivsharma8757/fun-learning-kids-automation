import os
import sys
import time
import subprocess
from config import VOICE_NAME, VOICE_RATE

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def get_audio_duration(audio_path):
    """Returns the duration of the audio file in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error reading audio duration with ffprobe: {e}")
        return 0.0

def generate_voice(voice_text, output_audio_path, output_vtt_path=None, max_retries=4):
    """
    Generates Hindi voice using edge-tts.
    Handles network dropouts with backoff retries.
    Validates output file size and ffprobe duration.
    """
    if os.path.exists(output_audio_path):
        try:
            os.remove(output_audio_path)
        except Exception:
            pass

    cmd = [
        "edge-tts",
        "--voice", VOICE_NAME,
        "--text", voice_text,
        "--write-media", output_audio_path
    ]
    if output_vtt_path:
        cmd.extend(["--write-subtitles", output_vtt_path])

    for attempt in range(1, max_retries + 1):
        print(f"🎙️ Generating voice narration (attempt {attempt}/{max_retries})...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode == 0 and os.path.exists(output_audio_path):
                file_size = os.path.getsize(output_audio_path)
                if file_size > 4000:
                    duration = get_audio_duration(output_audio_path)
                    if duration > 1.0:
                        print(f"✅ Voice generated successfully! ({duration:.2f}s, {file_size} bytes)")
                        return True, duration
                    else:
                        print(f"⚠️ Audio file is too short ({duration}s).")
                else:
                    print(f"⚠️ Audio file too small: {file_size} bytes.")
            else:
                err_msg = res.stderr.strip()[:200]
                print(f"⚠️ Edge-TTS failed on attempt {attempt}: {err_msg}")
        except subprocess.TimeoutExpired:
            print(f"⚠️ Edge-TTS timed out on attempt {attempt}.")
        except Exception as e:
            print(f"⚠️ Voice generation exception: {e}")

        if attempt < max_retries:
            wait_time = attempt * 4
            print(f"⏳ Retrying voice generation in {wait_time}s...")
            time.sleep(wait_time)

    return False, 0.0
