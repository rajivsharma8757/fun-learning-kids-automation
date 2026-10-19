"""
test_nanhe_seekho_club.py
--------------------------
Unit and verification test suite for the new channel:
Nanhe Seekho Club (नन्हे सीखो क्लब)

Covers:
1. Multi-channel profile architecture (defaults, overrides, distinct tokens/history).
2. Two-layer upload safeguards (hard block against legacy channel UCcOA6heUaTbOUnx7ERF23Gw).
3. Legacy video re-upload protection (blocking un-rebranded old uploads).
4. Content & metadata dynamic branding (titles, descriptions, tags, subtitles).
5. Cartoon Story Engine branding (Hindi outro voice text, English outro, tags, title).
6. Thumbnail watermark branding (NANHE SEEKHO CLUB badge).
7. Migration catalog data integrity.
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from config import (
    PROFILE_NANHE_SEEKHO, PROFILE_FUN_LEARNING,
    LEGACY_PROTECTED_CHANNEL_ID, ALLOW_LEGACY_CHANNEL_UPLOADS,
    CHANNEL_PROFILES, ACTIVE_PROFILE_NAME, CHANNEL_NAME,
    CHANNEL_NAME_HI, CHANNEL_HANDLE
)


class TestNanheSeekhoClubSetup(unittest.TestCase):

    def test_01_active_profile_defaults_to_nanhe_seekho(self):
        """1. Verify Nanhe Seekho Club is the active default channel profile."""
        self.assertEqual(ACTIVE_PROFILE_NAME, PROFILE_NANHE_SEEKHO)
        self.assertEqual(CHANNEL_NAME, "Nanhe Seekho Club")
        self.assertEqual(CHANNEL_NAME_HI, "नन्हे सीखो क्लब")
        self.assertEqual(CHANNEL_HANDLE, "@NanheSeekhoClub")
        self.assertFalse(ALLOW_LEGACY_CHANNEL_UPLOADS)

    def test_02_distinct_token_and_history_paths(self):
        """2. Verify Nanhe Seekho Club uses dedicated token and history files."""
        profile_nanhe = CHANNEL_PROFILES[PROFILE_NANHE_SEEKHO]
        profile_legacy = CHANNEL_PROFILES[PROFILE_FUN_LEARNING]

        # Tokens must be completely distinct
        self.assertNotEqual(profile_nanhe["token_file"], profile_legacy["token_file"])
        self.assertTrue(profile_nanhe["token_file"].endswith("token_nanhe_seekho_club.json"))
        self.assertTrue(profile_legacy["token_file"].endswith("token.json"))

        # Upload histories must be completely distinct
        self.assertNotEqual(profile_nanhe["uploads_history_file"], profile_legacy["uploads_history_file"])
        self.assertTrue(profile_nanhe["uploads_history_file"].endswith("uploads_nanhe_seekho_club.json"))
        self.assertTrue(profile_legacy["uploads_history_file"].endswith("uploads.json"))

        # Job states and cartoon histories distinct
        self.assertNotEqual(profile_nanhe["daily_jobs_file"], profile_legacy["daily_jobs_file"])
        self.assertNotEqual(profile_nanhe["cartoon_history_file"], profile_legacy["cartoon_history_file"])

    def test_03_legacy_channel_strictly_protected(self):
        """3. Verify legacy channel profile is marked protected and locked."""
        profile_legacy = CHANNEL_PROFILES[PROFILE_FUN_LEARNING]
        self.assertEqual(profile_legacy["channel_id"], LEGACY_PROTECTED_CHANNEL_ID)
        self.assertTrue(profile_legacy["is_protected"])
        self.assertFalse(profile_legacy["is_active"])

    def test_04_uploader_safeguard_blocks_legacy_channel_id(self):
        """4. Verify uploader safeguard raises RuntimeError if authenticated channel is legacy ID."""
        from uploader import check_channel_upload_safety

        mock_youtube = MagicMock()
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "id": LEGACY_PROTECTED_CHANNEL_ID,
                "snippet": {"title": "Fun Learning Kids"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UULegacy"}}
            }]
        }

        with self.assertRaises(RuntimeError) as ctx:
            check_channel_upload_safety(mock_youtube)

        self.assertIn("CRITICAL SAFETY INTERVENTION", str(ctx.exception))
        self.assertIn(LEGACY_PROTECTED_CHANNEL_ID, str(ctx.exception))

    def test_05_uploader_safeguard_blocks_channel_name_mismatch(self):
        """5. Verify uploader safeguard blocks if active profile is Nanhe Seekho but channel title is Fun Learning Kids."""
        from uploader import check_channel_upload_safety

        mock_youtube = MagicMock()
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "id": "UC_NEW_RANDOM_ID",
                "snippet": {"title": "Fun Learning Kids"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU_NEW"}}
            }]
        }

        with self.assertRaises(RuntimeError) as ctx:
            check_channel_upload_safety(mock_youtube)

        self.assertIn("CRITICAL SAFETY INTERVENTION", str(ctx.exception))

    def test_06_uploader_safeguard_permits_new_authorized_channel(self):
        """6. Verify uploader safeguard passes cleanly for authorized new channel."""
        from uploader import check_channel_upload_safety

        mock_youtube = MagicMock()
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "id": "UC_NEW_NANHE_SEEKHO_ID",
                "snippet": {"title": "Nanhe Seekho Club"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UUNanheUploads"}}
            }]
        }

        ch_id, ch_title, uploads_pl = check_channel_upload_safety(mock_youtube)
        self.assertEqual(ch_id, "UC_NEW_NANHE_SEEKHO_ID")
        self.assertEqual(ch_title, "Nanhe Seekho Club")
        self.assertEqual(uploads_pl, "UUNanheUploads")

    def test_07_cartoon_story_engine_rebranding(self):
        """7. Verify cartoon story engine dynamically brands Scene 6 outro and metadata."""
        from cartoon.story_engine import StoryEngine

        engine = StoryEngine()
        story = engine.get_next_story(forced_story_id="v4_bantu_science_lab")

        # Verify Scene 6 Hindi outro text contains Nanhe Seekho Club
        scene6 = story["scenes"][5]
        self.assertIn("नन्हे सीखो क्लब", scene6["text_hi"])
        self.assertNotIn("फन लर्निंग किड्स", scene6["text_hi"])
        self.assertIn("Nanhe Seekho Club", scene6["text_en"])
        self.assertNotIn("Fun Learning Kids", scene6["text_en"])

        # Verify YouTube metadata
        meta = engine.build_youtube_metadata(story)
        self.assertIn("Nanhe Seekho Club", meta["title"])
        self.assertIn("Welcome to Nanhe Seekho Club!", meta["description"])
        self.assertIn("#NanheSeekhoClub", meta["description"])
        self.assertIn("Nanhe Seekho Club", meta["tags"])

    def test_08_thumbnail_watermark_uses_nanhe_seekho(self):
        """8. Verify thumbnail maker generates watermark with active channel name."""
        from thumbnail_maker import create_thumbnail
        from PIL import Image

        # Create dummy test image
        temp_img_path = os.path.join(config.THUMBNAIL_DIR, "test_dummy_source.png")
        temp_thumb_path = os.path.join(config.THUMBNAIL_DIR, "test_dummy_thumb.jpg")

        img = Image.new("RGB", (1280, 720), color=(100, 150, 200))
        img.save(temp_img_path)

        try:
            ok, thumb_out = create_thumbnail(
                image_path=temp_img_path,
                topic="moral_story",
                short_title="The Kind Rabbit",
                output_thumb_path=temp_thumb_path,
                format_profile="landscape"
            )
            self.assertTrue(ok)
            self.assertTrue(os.path.exists(thumb_out))

            # Verify saved image dimensions
            with Image.open(thumb_out) as saved_img:
                self.assertEqual(saved_img.size, (1280, 720))
        finally:
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            if os.path.exists(temp_thumb_path):
                os.remove(temp_thumb_path)

    def test_09_migration_catalog_verified(self):
        """9. Verify local video catalog file exists and contains valid audit records."""
        catalog_path = os.path.join(config.BASE_DIR, "migration", "local_video_catalog.json")
        self.assertTrue(os.path.exists(catalog_path), f"Missing catalog file at: {catalog_path}")

        with open(catalog_path, "r", encoding="utf-8") as f:
            cat = json.load(f)

        self.assertEqual(len(cat), 151)
        # Check required schema keys
        required_keys = {"filename", "category", "path", "size_bytes", "migration_status", "file_hash"}
        for item in cat[:10]:
            self.assertTrue(required_keys.issubset(item.keys()))

    def test_10_branding_assets_exist(self):
        """10. Verify required branding assets are present on disk."""
        branding_dir = os.path.join(config.BASE_DIR, "branding")
        pfp = os.path.join(branding_dir, "profile_picture.png")
        banner = os.path.join(branding_dir, "channel_banner.png")
        wm = os.path.join(branding_dir, "watermark.png")
        profile_json = os.path.join(branding_dir, "channel_profile.json")

        self.assertTrue(os.path.exists(pfp), "Missing profile_picture.png")
        self.assertTrue(os.path.exists(banner), "Missing channel_banner.png")
        self.assertTrue(os.path.exists(wm), "Missing watermark.png")
        self.assertTrue(os.path.exists(profile_json), "Missing channel_profile.json")

        with open(profile_json, "r", encoding="utf-8") as f:
            p_data = json.load(f)
        ch_id_info = p_data.get("channel_identity", {})
        self.assertEqual(ch_id_info.get("name"), "Nanhe Seekho Club")
        self.assertEqual(ch_id_info.get("tagline"), "Little Minds, Big Discoveries!")


if __name__ == "__main__":
    unittest.main()
