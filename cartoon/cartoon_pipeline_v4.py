"""
cartoon_pipeline_v4.py
----------------------
Master Pipeline Runner for Cartoon Version 4: Production-Quality Kids Cartoon Engine.
Episode: "Mimi's Magic Toy Train" (मीमी और जादुई रेलगाड़ी).

Coordinates:
1. Redesigned compact subtitle SRT generation.
2. Master multi-track audio verification.
3. Multi-plane 1080p parallax scene rendering with grounded contact shadows,
   dynamic gaze tracking, and physical character acting.
4. High-CTR 1280x720 thumbnail creation.
5. Dual Technical & Visual Quality Gate inspection.
6. Keyframe extraction for all 6 scenes directly from the final MP4.

STRICT TEST MODE: Zero YouTube upload, Zero scheduler changes.
"""

import os
import sys
import json
import logging
import argparse
import subprocess

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    OUTPUT_DIR, THUMBNAILS_DIR, CARTOON_DIR
)
from cartoon.scene_renderer_v4 import SceneRendererV4
from cartoon.thumbnail_v4 import create_cartoon_thumbnail_v4
from cartoon.quality_gate_v4 import inspect_cartoon_v4
from cartoon.audio_mixer_v3 import build_final_audio_v3
from cartoon.subtitles import generate_subtitles_file

AUDIO_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3", "audio")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CartoonPipelineV4")


def extract_final_scene_frames(video_path):
    """Extracts actual frame captures from the final rendered MP4 at scene peaks."""
    times = [
        (1, 2.5),
        (2, 9.5),
        (3, 16.5),
        (4, 23.5),
        (5, 30.0),
        (6, 37.0)
    ]
    for s_id, t in times:
        out_p = os.path.join(OUTPUT_DIR, f"final_v4_scene{s_id}.jpg")
        cmd = ["ffmpeg", "-y", "-ss", str(t), "-i", video_path, "-vframes", "1", "-q:v", "2", out_p]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info("📸 Extracted all 6 final scene preview frames from MP4.")


def run_v4_demo():
    logger.info("==========================================================")
    logger.info("  STARTING CARTOON ANIMATION PIPELINE V4 (PRODUCTION POLISH)")
    logger.info("  Episode: Mimi's Magic Toy Train (मीमी और जादुई रेलगाड़ी)")
    logger.info("==========================================================")

    timing_file = os.path.join(AUDIO_V3_DIR, "timing_metadata.json")
    audio_master = os.path.join(AUDIO_V3_DIR, "final_master_audio_v3.wav")
    srt_file = os.path.join(OUTPUT_DIR, "demo_v4_subtitles.srt")
    video_file = os.path.join(OUTPUT_DIR, "demo_v4_mini_train.mp4")
    thumb_file = os.path.join(THUMBNAILS_DIR, "demo_v4_mini_train.jpg")

    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    # Step 1: Subtitles
    logger.info("📝 Generating Subtitles V4...")
    generate_subtitles_file(timing_meta, srt_file)

    # Step 2: Ensure Master Audio V3 is ready
    if not os.path.exists(audio_master):
        logger.info("🎵 Building Master Audio V3...")
        build_final_audio_v3()

    # Step 3: Render 2D Cartoon Animation Video V4
    logger.info("🎬 Rendering Version 4 Production Cartoon Animation Video...")
    renderer = SceneRendererV4()
    renderer.render_animation_video(timing_meta, audio_master, srt_file, video_file)

    # Step 4: Generate High-CTR Thumbnail V4
    logger.info("🎨 Generating Version 4 Thumbnail...")
    create_cartoon_thumbnail_v4(thumb_file)

    # Step 5: Extract actual MP4 scene frames
    extract_final_scene_frames(video_file)

    # Step 6: Run Dual Technical & Visual Quality Gate QA
    logger.info("🛡️ Running Dual Quality Gate QA...")
    qa_report = inspect_cartoon_v4(video_file, thumb_file)

    if qa_report["technical_passed"] and qa_report["visual_passed"]:
        logger.info("🎉 Cartoon Version 4 Production Demo completed successfully!")
    else:
        logger.warning("⚠️ Some Quality Gate checks failed. Please inspect report.")

    return qa_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cartoon Version 4 Pipeline")
    parser.add_argument("--demo", action="store_true", default=True, help="Run local demo without upload")
    args = parser.parse_args()
    run_v4_demo()
