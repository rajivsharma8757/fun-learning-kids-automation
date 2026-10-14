"""
test_audit_fixes.py
-------------------
Unit tests for the YouTube channel audit fixes:
1. Cartoon title deduplication & episode numbering
2. Zero-duration video rejection in validator
3. Dual format profiles (Landscape 16:9 vs Shorts 9:16)
4. Subtitle safe zone margins and thumbnail resolutions
5. Analytics reporter prerequisite checking and error handling
6. Baseline report data parsing and segmentations
7. Uploader duplicate title check
8. Uploader post-upload video processing status check
9. Analytics reporter traffic source and top video queries
10. Auth setup token inspection
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cartoon.story_engine import StoryEngine, STORY_BANK
import config
from video_validator import validate_video_file
from thumbnail_maker import create_thumbnail
from analytics_reporter import YouTubeAnalyticsReporter, REQUIRED_ANALYTICS_SCOPE
from uploader import check_duplicate_title, check_video_processing_status
import auth_setup


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
            mock_sub.return_value = MagicMock(
                returncode=0,
                stdout='{"streams": [{"codec_type": "video", "width": 1280, "height": 720, "duration": "0.00"}], "format": {"duration": "0.00"}}'
            )
            with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=50000):
                valid, err, dur, _ = validate_video_file("dummy.mp4", min_duration=1.0)
                self.assertFalse(valid)
                self.assertIn("shorter than minimum", err)

    def test_dual_format_profiles_and_dimensions(self):
        """Verify landscape and shorts format profiles have distinct, valid dimensions."""
        self.assertIn(config.FORMAT_LANDSCAPE, config.FORMAT_PROFILES)
        self.assertIn(config.FORMAT_SHORTS, config.FORMAT_PROFILES)

        land = config.FORMAT_PROFILES[config.FORMAT_LANDSCAPE]
        self.assertEqual(land['width'], 1280)
        self.assertEqual(land['height'], 720)
        self.assertEqual(land['aspect_ratio'], '16:9')
        self.assertFalse(land['tag_shorts'])
        self.assertIn("MarginV=36", land['subtitle_style'])

        shorts = config.FORMAT_PROFILES[config.FORMAT_SHORTS]
        self.assertEqual(shorts['width'], 1080)
        self.assertEqual(shorts['height'], 1920)
        self.assertEqual(shorts['aspect_ratio'], '9:16')
        self.assertTrue(shorts['tag_shorts'])
        self.assertIn("MarginV=260", shorts['subtitle_style'])  # Safe zone above Shorts UI

    def test_thumbnail_maker_dual_format(self):
        """Verify thumbnail generator creates correct aspect ratios for both landscape and shorts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            src_img = os.path.join(tmp_dir, "src.jpg")
            img = Image.new("RGB", (800, 600), color=(100, 150, 200))
            img.save(src_img)

            land_thumb = os.path.join(tmp_dir, "thumb_land.jpg")
            shorts_thumb = os.path.join(tmp_dir, "thumb_shorts.jpg")

            # Landscape
            ok_l, err_l = create_thumbnail(src_img, "good_habits", "Clean Toys", land_thumb, format_profile="landscape")
            self.assertTrue(ok_l, f"Landscape thumb failed: {err_l}")
            with Image.open(land_thumb) as im:
                self.assertEqual(im.size, (1280, 720))

            # Shorts
            ok_s, err_s = create_thumbnail(src_img, "good_habits", "Clean Toys", shorts_thumb, format_profile="shorts")
            self.assertTrue(ok_s, f"Shorts thumb failed: {err_s}")
            with Image.open(shorts_thumb) as im:
                self.assertEqual(im.size, (1080, 1920))

    def test_analytics_reporter_prerequisites_and_status(self):
        """Verify analytics reporter identifies missing scopes and disabled API without crashing."""
        reporter = YouTubeAnalyticsReporter()
        ok, msg = reporter.check_prerequisites()
        self.assertFalse(ok)
        self.assertIn("BLOCKED_SCOPE_PENDING", reporter.auth_status)
        self.assertIn(REQUIRED_ANALYTICS_SCOPE, msg)

        # Verify query_channel_overview reports blocked status cleanly
        res = reporter.query_channel_overview()
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("console.developers.google.com", res["gcp_enable_url"])

    def test_analytics_baseline_report_structure(self):
        """Verify baseline report parses video dataset and segments by topic and format."""
        reporter = YouTubeAnalyticsReporter()
        report = reporter.generate_baseline_report()

        self.assertIn("totals", report)
        self.assertIn("format_breakdown", report)
        self.assertIn("duration_buckets", report)
        self.assertIn("topic_breakdown", report)
        self.assertIn("top_viewed_videos", report)

        self.assertEqual(report["totals"]["total_videos"], 100)
        self.assertEqual(report["totals"]["total_views"], 50)
        self.assertEqual(report["format_breakdown"]["landscape_16_9"]["count"], 100)
        self.assertEqual(report["format_breakdown"]["shorts_9_16"]["count"], 0)

    def test_uploader_check_duplicate_title(self):
        """Verify check_duplicate_title detects duplicate titles regardless of extra whitespace/casing."""
        history = [
            {"title": "Good Habits for Kids | Wash Hands", "video_id": "VID_123"},
            {"title": "Bantu Robot | Science Lab Ep 1", "video_id": "VID_456"}
        ]
        # Match case-insensitive
        is_dupe, count, rec = check_duplicate_title("good habits for kids | wash hands", history=history)
        self.assertTrue(is_dupe)
        self.assertEqual(count, 1)
        self.assertEqual(rec["video_id"], "VID_123")

        # Unique title
        is_dupe, count, rec = check_duplicate_title("Brand New Episode | Good Morning", history=history)
        self.assertFalse(is_dupe)
        self.assertEqual(count, 0)
        self.assertIsNone(rec)

    def test_uploader_check_video_processing_status(self):
        """Verify check_video_processing_status handles succeeded and rejected statuses."""
        mock_youtube = MagicMock()

        # 1. Successful processing
        mock_youtube.videos().list().execute.return_value = {
            "items": [{
                "status": {"uploadStatus": "processed"},
                "processingDetails": {"processingStatus": "succeeded"}
            }]
        }
        up_st, rej, proc_st = check_video_processing_status(mock_youtube, "VID_OK", max_wait_sec=1)
        self.assertEqual(up_st, "processed")
        self.assertIsNone(rej)
        self.assertEqual(proc_st, "succeeded")

        # 2. Rejected video
        mock_youtube.videos().list().execute.return_value = {
            "items": [{
                "status": {"uploadStatus": "rejected", "rejectionReason": "duplicate"},
                "processingDetails": {"processingStatus": "failed"}
            }]
        }
        up_st, rej, proc_st = check_video_processing_status(mock_youtube, "VID_REJ", max_wait_sec=1)
        self.assertEqual(up_st, "rejected")
        self.assertEqual(rej, "duplicate")

    def test_analytics_reporter_traffic_and_top_queries(self):
        """Verify query_traffic_sources and query_top_videos handle blocked state and mock responses."""
        reporter = YouTubeAnalyticsReporter()

        # When blocked (no analytics scope in token.json)
        traffic = reporter.query_traffic_sources()
        self.assertEqual(traffic["status"], "BLOCKED")

        top = reporter.query_top_videos()
        self.assertEqual(top["status"], "BLOCKED")

        # With mock service
        mock_service = MagicMock()
        mock_service.reports().query().execute.return_value = {"rows": [["SEARCH", 25]]}
        with patch.object(reporter, "get_service", return_value=(mock_service, None)):
            res_t = reporter.query_traffic_sources()
            self.assertEqual(res_t["status"], "SUCCESS")
            self.assertIn("rows", res_t["data"])

            res_v = reporter.query_top_videos()
            self.assertEqual(res_v["status"], "SUCCESS")

    def test_auth_setup_inspect_token(self):
        """Verify auth_setup safely inspects existing token without exposing secrets."""
        exists, scopes, valid = auth_setup.inspect_current_token()
        self.assertTrue(exists)
        self.assertTrue(valid)
        self.assertIsInstance(scopes, list)


if __name__ == "__main__":
    unittest.main()
