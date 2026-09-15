"""
cartoon_pipeline.py
-------------------
Master orchestrator for the "Fun Learning Kids" Cartoon Animation System (Video 3).
Operates 100% independently from Video 1 & Video 2 daily automation.

Modes:
- Demo / Test Mode: Renders local demo episode ("Chintu Learns to Share") without YouTube upload.
- Full Daily Mode (when activated in future): Generates daily cartoon, mixes audio, burns subtitles, creates thumbnail, and handles isolated upload if enabled.
"""

import os
import sys
import json
import argparse
import logging

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    CARTOON_DIR, AUDIO_DIR, OUTPUT_DIR, THUMBNAILS_DIR,
    CARTOON_TOPICS
)
from cartoon.subtitles import generate_subtitles_file
from cartoon.thumbnail import create_cartoon_thumbnail
from cartoon.scene_renderer import SceneRenderer
from cartoon.quality_gate import inspect_cartoon_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CartoonPipeline")


def run_demo_pipeline():
    """
    Renders and verifies the high-quality local demo cartoon episode:
    'Chintu Learns to Share' (चिंटू ने सीखा बाँटना).
    STRICTLY LOCAL: No YouTube upload.
    """
    logger.info("==================================================")
    logger.info("  STARTING CARTOON ANIMATION PIPELINE (DEMO MODE)")
    logger.info("  Episode: Chintu Learns to Share (चिंटू ने सीखा बाँटना)")
    logger.info("==================================================")

    timing_file = os.path.join(AUDIO_DIR, "timing_metadata.json")
    audio_file = os.path.join(AUDIO_DIR, "final_master_audio.wav")
    srt_file = os.path.join(OUTPUT_DIR, "demo_subtitles.srt")
    video_file = os.path.join(OUTPUT_DIR, "demo_chintu_shares.mp4")
    thumb_file = os.path.join(THUMBNAILS_DIR, "demo_chintu_shares.jpg")

    # Step 1: Verify audio & timing assets
    if not os.path.exists(timing_file) or not os.path.exists(audio_file):
        raise FileNotFoundError(f"Missing required audio master files in {AUDIO_DIR}")

    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    # Step 2: Ensure subtitles exist
    if not os.path.exists(srt_file):
        logger.info("Generating English subtitles...")
        generate_subtitles_file(timing_meta, srt_file)

    # Step 3: Render animation video
    logger.info("Rendering 2D cartoon animation video...")
    renderer = SceneRenderer()
    renderer.render_animation_video(timing_meta, audio_file, srt_file, video_file)

    # Step 4: Generate YouTube Thumbnail
    logger.info("Generating high-CTR thumbnail...")
    create_cartoon_thumbnail(thumb_file)

    # Step 5: Run Automated Quality Gate
    logger.info("Running Quality Gate QA verification...")
    qa_report = inspect_cartoon_video(video_file, thumb_file)

    if qa_report["passed"]:
        logger.info("🎉 Cartoon demo pipeline completed successfully!")
    else:
        logger.warning("⚠️ Some Quality Gate checks failed. Please inspect report.")

    return qa_report


def main():
    parser = argparse.ArgumentParser(description="Fun Learning Kids Cartoon Animation Pipeline")
    parser.add_argument("--demo", action="store_true", default=True, help="Run local demo episode without upload")
    args = parser.parse_args()

    run_demo_pipeline()


if __name__ == "__main__":
    main()
