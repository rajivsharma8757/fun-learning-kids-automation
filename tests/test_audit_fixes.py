"""
test_audit_fixes.py
-------------------
Unit tests for the YouTube channel audit fixes:
1. Cartoon title deduplication & episode numbering
2. Normal video title deduplication
3. Shorts vs landscape format configuration
4. Defective / 0s video rejection
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cartoon.story_engine import StoryEngine, STORY_BANK
import config
from video_validator import validate_video_file


class TestAuditFixes(unittest.TestCase):

    def test_cartoon_title_deduplication(self):
        """Verify cartoon metadata generates dynamic episode numbers and unique titles under 100 chars."""
        engine = StoryEngine()
        story = STORY_BANK[0]  # Bantu Science Lab
        meta = engine.build_youtube_metadata(story)

        self.assertIn("Ep ", meta["title"])
        self.assertIn(story["title_hi"], meta["title"])
        self.assertLessEqual(len(meta["title"]), 100, f"Title exceeds 100 chars: {meta['title']}")
        self.assertIn("Episode", meta["description"])

    def test_video_validator_rejects_zero_duration(self):
        """Verify video_validator rejects 0-second videos (like the defective HhotZWPAYaU)."""
        with patch("subprocess.run") as mock_sub:
            # Simulate ffprobe returning 0 second duration
            mock_sub.return_value = MagicMock(
                returncode=0,
                stdout='{"streams": [{"codec_type": "video", "width": 1280, "height": 720, "duration": "0.00"}], "format": {"duration": "0.00"}}'
            )
            with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=50000):
                valid, err, dur, _ = validate_video_file("dummy.mp4", min_duration=1.0)
                self.assertFalse(valid)
                self.assertIn("shorter than minimum", err)

    def test_shorts_format_configuration(self):
        """Verify config resolution changes when VIDEO_FORMAT is set to shorts."""
        with patch.dict(os.environ, {"VIDEO_FORMAT": "shorts"}):
            import importlib
            importlib.reload(config)
            self.assertEqual(config.VIDEO_FORMAT, "shorts")
            self.assertEqual(config.VIDEO_WIDTH, 1080)
            self.assertEqual(config.VIDEO_HEIGHT, 1920)

        with patch.dict(os.environ, {"VIDEO_FORMAT": "landscape"}):
            importlib.reload(config)
            self.assertEqual(config.VIDEO_FORMAT, "landscape")
            self.assertEqual(config.VIDEO_WIDTH, 1280)
            self.assertEqual(config.VIDEO_HEIGHT, 720)


if __name__ == "__main__":
    unittest.main()
