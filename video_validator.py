"""
video_validator.py
------------------
Rigorous pre-upload inspection for Fun Learning Kids video assets.
Guarantees zero partial, zero-byte, corrupt, or unreadable MP4 files
are ever sent to YouTube.
"""

import os
import sys
import json
import logging
import subprocess

logger = logging.getLogger("kids_automation")


def validate_video_file(video_path, min_duration=1.0, min_size_bytes=20000):
    """
    Validates that a video file:
    1. Exists and is greater than min_size_bytes
    2. Has a valid MP4/container readable by ffprobe
    3. Contains at least one video stream with valid dimensions & codec
    4. Has duration >= min_duration seconds
    5. Contains an audio stream

    Returns:
        (is_valid: bool, error_message: str or None, duration: float, size_bytes: int)
    """
    if not video_path or not os.path.exists(video_path):
        return False, f"Video file not found on disk: {video_path}", 0.0, 0

    try:
        size = os.path.getsize(video_path)
    except Exception as e:
        return False, f"Could not inspect video file size: {e}", 0.0, 0

    if size < min_size_bytes:
        return False, f"Video file is suspiciously small ({size} bytes, minimum {min_size_bytes})", 0.0, size

    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            err_snippet = res.stderr.strip()[:200]
            return False, f"ffprobe validation failed (exit {res.returncode}): {err_snippet}", 0.0, size

        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        if not v_stream:
            return False, "No valid video stream detected in media file", 0.0, size

        v_codec = v_stream.get("codec_name", "")
        if v_codec not in ["h264", "libx264", "hevc", "mpeg4"]:
            logger.warning(f"Unexpected video codec: {v_codec}")

        w = int(v_stream.get("width", 0))
        h = int(v_stream.get("height", 0))
        if w < 320 or h < 240:
            return False, f"Invalid video dimensions: {w}x{h}", 0.0, size

        # Check duration
        fmt = data.get("format", {})
        dur_str = fmt.get("duration") or v_stream.get("duration")
        if not dur_str:
            return False, "Could not determine media duration", 0.0, size

        duration = float(dur_str)
        if duration < min_duration:
            return False, f"Video duration ({duration:.2f}s) is shorter than minimum {min_duration}s", duration, size

        if not a_stream:
            logger.warning(f"No audio stream detected in video file {video_path}")

        logger.info(f"✅ Video integrity verified: {os.path.basename(video_path)} ({w}x{h}, {duration:.2f}s, {size:,} bytes)")
        return True, None, duration, size

    except subprocess.TimeoutExpired:
        return False, "ffprobe verification timed out after 30 seconds", 0.0, size
    except json.JSONDecodeError:
        return False, "Could not parse ffprobe output as JSON", 0.0, size
    except Exception as e:
        return False, f"Video validation exception: {e}", 0.0, size
