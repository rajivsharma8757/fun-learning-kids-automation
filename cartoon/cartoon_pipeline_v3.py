"""
cartoon_pipeline_v3.py
----------------------
Master Pipeline Runner for Cartoon Version 3: Real Professional Kids Cartoon Engine.
Episode: "Mimi's Magic Toy Train" (मीमी और जादुई रेलगाड़ी).
Coordinates:
1. Subtitle SRT generation.
2. Master multi-track audio verification.
3. Multi-plane 1080p parallax scene rendering with physical acting.
4. High-CTR 1280x720 thumbnail creation.
5. 22-Point Quality Gate QA inspection.
STRICT TEST MODE: Zero YouTube upload, Zero scheduler changes.
"""

import os
import sys
import json
import logging
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    OUTPUT_DIR, THUMBNAILS_DIR, CARTOON_DIR
)
from cartoon.scene_renderer_v3 import SceneRendererV3
from cartoon.thumbnail_v3 import create_cartoon_thumbnail_v3
from cartoon.quality_gate_v3 import inspect_cartoon_v3
from cartoon.audio_mixer_v3 import build_final_audio_v3
from cartoon.subtitles import generate_subtitles_file

AUDIO_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3", "audio")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CartoonPipelineV3")


def run_v3_demo():
    logger.info("==========================================================")
    logger.info("  STARTING CARTOON ANIMATION PIPELINE V3 (DEMO MODE)")
    logger.info("  Episode: Mimi's Magic Toy Train (मीमी और जादुई रेलगाड़ी)")
    logger.info("==========================================================")

    timing_file = os.path.join(AUDIO_V3_DIR, "timing_metadata.json")
    audio_master = os.path.join(AUDIO_V3_DIR, "final_master_audio_v3.wav")
    srt_file = os.path.join(OUTPUT_DIR, "demo_v3_subtitles.srt")
    video_file = os.path.join(OUTPUT_DIR, "demo_v3_mini_train.mp4")
    thumb_file = os.path.join(THUMBNAILS_DIR, "demo_v3_mini_train.jpg")

    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    # Step 1: Ensure Subtitles are generated
    logger.info("📝 Generating Subtitles V3...")
    generate_subtitles_file(timing_meta, srt_file)

    # Step 2: Ensure Master Audio V3 is built
    if not os.path.exists(audio_master):
        logger.info("🎵 Building Master Audio V3...")
        build_final_audio_v3()

    # Step 3: Render 2D Cartoon Animation Video V3
    logger.info("🎬 Rendering Version 3 Cartoon Animation Video...")
    renderer = SceneRendererV3()
    renderer.render_animation_video(timing_meta, audio_master, srt_file, video_file)

    # Step 4: Generate High-CTR Thumbnail V3
    logger.info("🎨 Generating Version 3 Thumbnail...")
    create_cartoon_thumbnail_v3(thumb_file)

    # Step 5: Run 22-Point Automated Quality Gate QA
    logger.info("🛡️ Running 22-Point Quality Gate QA...")
    qa_report = inspect_cartoon_v3(video_file, thumb_file)

    if qa_report["passed"]:
        logger.info("🎉 Cartoon Version 3 Demo Pipeline completed successfully!")
    else:
        logger.warning("⚠️ Some Quality Gate checks failed. Please inspect report.")

    return qa_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cartoon Version 3 Pipeline")
    parser.add_argument("--demo", action="store_true", default=True, help="Run local demo without upload")
    args = parser.parse_args()
    run_v3_demo()
