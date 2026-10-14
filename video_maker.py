import os
import sys
import subprocess
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, SUBTITLE_STYLE

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def generate_srt_file(subtitles_list, duration, output_srt_path):
    """Creates a cleanly timed SRT file from a list of English sentences."""
    if not subtitles_list:
        return False

    n = len(subtitles_list)
    slot_dur = duration / n
    lines = []

    for i, text in enumerate(subtitles_list):
        start = i * slot_dur + 0.2
        end = min((i + 1) * slot_dur - 0.1, duration - 0.1)
        if end <= start:
            end = start + 0.5
        lines.append(f"{i + 1}")
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(text.strip())
        lines.append("")

    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True

def create_video(image_path, audio_path, srt_path, output_video_path, audio_duration, format_profile=None):
    """
    Creates high quality MP4 video using FFmpeg.
    - format_profile: 'landscape' (1280x720, 16:9) or 'shorts' (1080x1920, 9:16).
      Defaults to config.DEFAULT_FORMAT ('landscape').
    - Preserves aspect ratio with blurred background padding
    - Burns styled child-friendly English subtitles positioned for target format
    - Uses H.264 (yuv420p) and AAC audio
    - Matches audio duration precisely (-t)
    - Strictly checks exit code, dimensions, and file integrity
    """
    from config import FORMAT_PROFILES, DEFAULT_FORMAT
    prof = FORMAT_PROFILES.get(format_profile or DEFAULT_FORMAT, FORMAT_PROFILES[DEFAULT_FORMAT])
    w = prof['width']
    h = prof['height']
    fps = prof['fps']
    sub_style = prof['subtitle_style']

    if os.path.exists(output_video_path):
        try:
            os.remove(output_video_path)
        except Exception:
            pass

    # Build filter complex for background blur + foreground center
    filter_chains = [
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:5[bg]",
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease[fg]",
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
    ]

    last_link = "[base]"
    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        sub_filter = f"subtitles='{escaped_srt}':force_style='{sub_style}'"
        filter_chains.append(f"{last_link}{sub_filter}[v]")
        last_link = "[v]"

    filter_complex = ";".join(filter_chains)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-t", f"{audio_duration:.2f}",
        "-filter_complex", filter_complex,
        "-map", last_link,
        "-map", "1:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video_path
    ]

    print(f"🎬 Rendering video with FFmpeg (Profile: {prof['name']} {w}x{h})...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            err = res.stderr[-500:].strip()
            print(f"❌ FFmpeg failed with code {res.returncode}: {err}")
            return False, f"FFmpeg error: {err}"

        if not os.path.exists(output_video_path):
            print("❌ Output video file was not created.")
            return False, "Output video missing"

        size = os.path.getsize(output_video_path)
        if size < 20000:
            print(f"❌ Output video file too small: {size} bytes")
            return False, f"Output video too small: {size} bytes"

        # Verify video with ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration:format=duration",
            "-of", "json",
            output_video_path
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        import json
        probe_data = json.loads(probe_res.stdout)
        v_stream = probe_data.get("streams", [{}])[0]
        actual_w = int(v_stream.get("width", 0))
        actual_h = int(v_stream.get("height", 0))
        video_dur = float(probe_data.get("format", {}).get("duration") or v_stream.get("duration", 0))

        if actual_w != w or actual_h != h:
            err_dim = f"Rendered video dimensions {actual_w}x{actual_h} do not match expected {w}x{h}"
            print(f"❌ {err_dim}")
            return False, err_dim

        print(f"✅ Video created successfully: {output_video_path} ({actual_w}x{actual_h}, {video_dur:.2f}s, {size} bytes, profile={prof['name']})")
        return True, None

    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out after 120s.")
        return False, "FFmpeg render timeout"
    except Exception as e:
        print(f"❌ Video creation exception: {e}")
        return False, str(e)
