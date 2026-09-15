"""
cartoon_pipeline_v2.py
----------------------
Master Pipeline Runner for Cartoon Version 2: Professional Kids Animation.
Coordinates asset validation, scene rendering, thumbnail generation, and Quality Gate QA.
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
    AUDIO_DIR, OUTPUT_DIR, THUMBNAILS_DIR
)
from cartoon.scene_renderer_v2 import SceneRendererV2
from cartoon.thumbnail_v2 import create_cartoon_thumbnail_v2
from cartoon.quality_gate_v2 import inspect_cartoon_v2
from cartoon.audio_mixer_v2 import build_final_audio_v2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("CartoonPipelineV2")


def run_v2_demo():
    logger.info("==========================================================")
    logger.info("  STARTING CARTOON ANIMATION PIPELINE V2 (DEMO MODE)")
    logger.info("  Episode: Chintu Learns to Share (चिंटू ने सीखा बाँटना)")
    logger.info("==========================================================")

    timing_file = os.path.join(AUDIO_DIR, "timing_metadata.json")
    audio_master = os.path.join(AUDIO_DIR, "final_master_audio_v2.wav")
    srt_file = os.path.join(OUTPUT_DIR, "demo_subtitles.srt")
    video_file = os.path.join(OUTPUT_DIR, "demo_v2_chintu_shares.mp4")
    thumb_file = os.path.join(THUMBNAILS_DIR, "demo_v2_chintu_shares.jpg")

    # Step 1: Ensure Master Audio V2 is built
    if not os.path.exists(audio_master):
        logger.info("Building Master Audio V2...")
        build_final_audio_v2()

    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    # Step 2: Render 2D Cartoon Animation Video V2
    logger.info("🎬 Rendering Version 2 Cartoon Animation Video...")
    renderer = SceneRendererV2()
    renderer.render_animation_video(timing_meta, audio_master, srt_file, video_file)

    # Step 3: Generate High-CTR Thumbnail V2
    logger.info("🎨 Generating Version 2 Thumbnail...")
    create_cartoon_thumbnail_v2(thumb_file)

    # Step 4: Run 20-Point Automated Quality Gate QA
    logger.info("🛡️ Running 20-Point Quality Gate QA...")
    qa_report = inspect_cartoon_v2(video_file, thumb_file)

    if qa_report["passed"]:
        logger.info("🎉 Cartoon Version 2 Demo Pipeline completed successfully!")
    else:
        logger.warning("⚠️ Some Quality Gate checks failed. Please inspect report.")

    return qa_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cartoon Version 2 Pipeline")
    parser.add_argument("--demo", action="store_true", default=True, help="Run local demo without upload")
    args = parser.parse_args()
    run_v2_demo()
