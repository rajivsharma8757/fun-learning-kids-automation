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

def create_video(image_path, audio_path, srt_path, output_video_path, audio_duration):
    """
    Creates high quality MP4 video using FFmpeg.
    - Preserves aspect ratio with blurred background padding
    - Burns styled child-friendly English subtitles
    - Uses H.264 (yuv420p) and AAC audio
    - Matches audio duration precisely (-t)
    - Strictly checks exit code and file integrity
    """
    if os.path.exists(output_video_path):
        try:
            os.remove(output_video_path)
        except Exception:
            pass

    # Build filter complex for background blur + foreground center
    filter_chains = [
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=20:5[bg]",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease[fg]",
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
    ]

    last_link = "[base]"
    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        sub_filter = f"subtitles='{escaped_srt}':force_style='{SUBTITLE_STYLE}'"
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
        "-r", str(VIDEO_FPS),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_video_path
    ]

    print("🎬 Rendering video with FFmpeg...")
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
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            output_video_path
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        video_dur = float(probe_res.stdout.strip())
        
        print(f"✅ Video created successfully: {output_video_path} ({video_dur:.2f}s, {size} bytes)")
        return True, None

    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out after 120s.")
        return False, "FFmpeg render timeout"
    except Exception as e:
        print(f"❌ Video creation exception: {e}")
        return False, str(e)
