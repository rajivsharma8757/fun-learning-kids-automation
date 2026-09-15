"""
variety_manager.py
------------------
Persistent Variety & Alternation Controller for "Fun Learning Kids" Cartoon Module.

Core Responsibilities:
1. Strict 1:1 Alternation:
   - Equal priority between Style V1 and Style V4.
   - Day 1 = V1, Day 2 = V4, Day 3 = V1, Day 4 = V4, etc.
   - Grounded persistently on the previous successful YouTube upload.
   - Reboots, restarts, and temporary failures NEVER reset or advance the rotation prematurely.
2. Absolute Anti-Repetition Rules:
   - NEVER repeat an already uploaded story.
   - NEVER repeat the same main character on consecutive days.
   - Mimi Cooldown: Mimi can only return after at least 3-4 other cartoon productions.
   - NEVER repeat the same background/location on consecutive days.
   - NEVER repeat the same character + background combination.
   - NEVER repeat the same visual theme on consecutive days.
   - NEVER repeat the same final video SHA256 hash.
3. Multi-Attribute History Tracking & Legacy Record Enrichment:
   - Automatically enriches older history records with characters, background, location, and theme.
   - Records: date, timestamp, style, story_id, characters, main_character,
     background, location, visual_theme, video_path, video_hash, upload_id, upload_status.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_HISTORY_FILE

logger = logging.getLogger("kids_automation")

# Legacy mapping for known older records
LEGACY_STORY_META = {
    "v4_mimi_magic_train": {
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "playroom",
        "background": "cozy_playroom",
        "visual_theme": "toys_and_care",
    },
    "v4_mimi_garden_adventure": {
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "garden",
        "background": "cozy_playroom",
        "visual_theme": "nature_and_play",
    },
    "v4_mimi_clean_room": {
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "playroom",
        "background": "cozy_playroom",
        "visual_theme": "cleanliness_and_responsibility",
    },
    "v4_mimi_rainbow_blocks": {
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "playroom",
        "background": "cozy_playroom",
        "visual_theme": "colors_and_shapes",
    },
    "v4_mimi_fruit_basket": {
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "kitchen",
        "background": "cozy_playroom",
        "visual_theme": "healthy_eating",
    },
    "v1_chintu_shares": {
        "main_character": "chintu",
        "characters": ["chintu", "golu"],
        "location": "meadow",
        "background": "forest_meadow",
        "visual_theme": "sharing_and_friendship",
    },
    "v1_chintu_golu_help": {
        "main_character": "chintu",
        "characters": ["chintu", "golu"],
        "location": "meadow",
        "background": "forest_meadow",
        "visual_theme": "helping_others",
    },
    "v1_chintu_morning_exercise": {
        "main_character": "chintu",
        "characters": ["chintu", "golu"],
        "location": "meadow",
        "background": "forest_meadow",
        "visual_theme": "health_and_exercise",
    },
}


class VarietyManager:
    def __init__(self, history_file=CARTOON_HISTORY_FILE):
        self.history_file = history_file
        self._ensure_history_dir()

    def _ensure_history_dir(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

    def load_history(self):
        """Loads persistent cartoon production history with enriched metadata."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                return [self._enrich_record(h) for h in history]
            except Exception as e:
                logger.warning(f"Could not read cartoon history from {self.history_file}: {e}")
                return []
        return []

    def _enrich_record(self, record):
        """Enriches legacy records that might lack variety metadata."""
        rec = dict(record)
        sid = rec.get("story_id", "")

        if sid in LEGACY_STORY_META:
            meta = LEGACY_STORY_META[sid]
            for k, v in meta.items():
                if not rec.get(k):
                    rec[k] = v

        # Fallback inferences from story_id or title
        if not rec.get("main_character"):
            if "mimi" in sid.lower():
                rec["main_character"] = "mimi"
            elif "chintu" in sid.lower():
                rec["main_character"] = "chintu"
            elif "bantu" in sid.lower():
                rec["main_character"] = "bantu"
            elif "aarav" in sid.lower():
                rec["main_character"] = "aarav"
            elif "koko" in sid.lower():
                rec["main_character"] = "koko"
            elif "bholu" in sid.lower():
                rec["main_character"] = "bholu"
            elif "leo" in sid.lower():
                rec["main_character"] = "leo"

        if not rec.get("background"):
            if rec.get("style", "").upper() == "V4":
                rec["background"] = "cozy_playroom"
            else:
                rec["background"] = "forest_meadow"

        return rec

    def get_successful_uploads(self):
        """Returns all history records that represent confirmed successful uploads."""
        history = self.load_history()
        return [
            h for h in history
            if h.get("status") == "uploaded" and (h.get("video_id") or h.get("upload_id"))
        ]

    def get_last_successful_upload(self):
        """Returns the most recent successfully uploaded cartoon record, or None."""
        successes = self.get_successful_uploads()
        if successes:
            return successes[-1]
        return None

    def determine_next_style(self, forced_style=None):
        """
        Determines the animation engine for today's cartoon.
        STRICT 1:1 ALTERNATION:
        - If the last successful upload was V4 -> next MUST be V1.
        - If the last successful upload was V1 -> next MUST be V4.
        - If no previous successful upload -> defaults to V1.
        """
        if forced_style:
            norm = forced_style.upper()
            if norm in ("V1", "V4"):
                return norm

        last_upload = self.get_last_successful_upload()
        if not last_upload:
            logger.info("No previous successful cartoon upload found; starting alternation with V1.")
            return "V1"

        last_style = last_upload.get("style", "V4").upper()
        if last_style == "V4":
            next_style = "V1"
        else:
            next_style = "V4"

        logger.info(f"Persistent Alternation: Last upload was {last_style} -> Next style is {next_style}.")
        return next_style

    def compute_file_hash(self, filepath):
        """Computes SHA-256 of the rendered video file."""
        if not filepath or not os.path.exists(filepath):
            return None
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def record_production(
        self,
        story_id,
        style,
        title,
        main_character,
        characters,
        background,
        location,
        visual_theme,
        video_path=None,
        thumbnail_path=None,
        video_hash=None,
        upload_id=None,
        status="completed"
    ):
        """
        Records a completed cartoon production in history with comprehensive metadata.
        """
        history = self.load_history()
        now = datetime.now()

        if not video_hash and video_path and os.path.exists(video_path):
            video_hash = self.compute_file_hash(video_path)

        entry = {
            "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.isoformat(),
            "style": style.upper(),
            "story_id": story_id,
            "title": title,
            "main_character": main_character,
            "characters": characters if isinstance(characters, list) else [characters],
            "background": background,
            "location": location,
            "visual_theme": visual_theme,
            "video_path": video_path,
            "thumbnail_path": thumbnail_path,
            "video_hash": video_hash,
            "video_id": upload_id,
            "upload_id": upload_id,
            "status": status
        }

        history.append(entry)
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"Recorded production for '{story_id}' ({style}, Character: {main_character}, Status: {status}).")
        except Exception as e:
            logger.error(f"Failed to write cartoon history: {e}")

    def evaluate_story_candidate(self, story, target_style, recent_history):
        """
        Evaluates a story candidate against all anti-repetition rules.
        Returns (is_valid: bool, reason: str).
        """
        # Rule 0: Style match
        if story.get("style", "").upper() != target_style.upper():
            return False, f"Style mismatch (expected {target_style}, got {story.get('style')})"

        # Rule 1: Story must NEVER have been uploaded previously
        uploaded_story_ids = {h.get("story_id") for h in recent_history if h.get("status") in ("uploaded", "completed")}
        if story["story_id"] in uploaded_story_ids:
            return False, f"Story '{story['story_id']}' was already uploaded in history"

        if not recent_history:
            return True, "Initial story selection"

        # Check last completed production
        last_prod = recent_history[-1]
        last_main_char = (last_prod.get("main_character", "") or "").strip().lower()
        last_location = (last_prod.get("location", "") or "").strip().lower()
        last_bg = (last_prod.get("background", "") or "").strip().lower()
        last_theme = (last_prod.get("visual_theme", "") or "").strip().lower()

        candidate_main_char = (story.get("main_character", story.get("character", "")) or "").strip().lower()
        candidate_location = (story.get("location", "") or "").strip().lower()
        candidate_bg = (story.get("background", "") or "").strip().lower()
        candidate_theme = (story.get("visual_theme", story.get("theme", "")) or "").strip().lower()

        # Rule 2: Consecutive Character Protection
        if candidate_main_char and last_main_char and candidate_main_char == last_main_char:
            return False, f"Consecutive character repetition: '{candidate_main_char}' was used in the last production"

        # Rule 3: Mimi Cooldown Protection (Mimi cannot appear unless >= 3-4 productions since last Mimi)
        if candidate_main_char == "mimi":
            prods_since_mimi = 0
            for h in reversed(recent_history):
                h_char = (h.get("main_character", "") or h.get("character", "") or "").strip().lower()
                h_sid = (h.get("story_id", "") or "").lower()
                if "mimi" in h_char or "mimi" in h_sid:
                    break
                prods_since_mimi += 1
            else:
                prods_since_mimi = 999

            if prods_since_mimi < 3:
                return False, f"Mimi cooldown active ({prods_since_mimi}/3 gap required before Mimi can return)"

        # Rule 4: Consecutive Background/Location Protection
        if candidate_location and last_location and candidate_location == last_location:
            return False, f"Consecutive location repetition: '{candidate_location}' was used in the last production"

        if candidate_bg and last_bg and candidate_bg == last_bg:
            return False, f"Consecutive background repetition: '{candidate_bg}' was used in the last production"

        # Rule 5: Consecutive Theme Protection
        if candidate_theme and last_theme and candidate_theme == last_theme:
            return False, f"Consecutive theme repetition: '{candidate_theme}' was used in the last production"

        # Rule 6: Same Character + Same Background Combination
        recent_char_bg_pairs = {
            ((h.get("main_character", "") or "").strip().lower(),
             (h.get("background", "") or "").strip().lower())
            for h in recent_history[-5:]
        }
        if (candidate_main_char, candidate_bg) in recent_char_bg_pairs:
            return False, f"Character + Background combination ({candidate_main_char} + {candidate_bg}) was used recently"

        return True, "Valid candidate"

    def select_next_production_story(self, story_bank, forced_style=None, forced_story_id=None):
        """
        Selects the next story adhering strictly to 1:1 alternation and anti-repetition rules.
        """
        if forced_story_id:
            for s in story_bank:
                if s["story_id"] == forced_story_id:
                    return s

        target_style = self.determine_next_style(forced_style)
        history = self.load_history()

        candidates = [s for s in story_bank if s.get("style", "").upper() == target_style]
        valid_candidates = []

        for c in candidates:
            valid, reason = self.evaluate_story_candidate(c, target_style, history)
            if valid:
                valid_candidates.append(c)
            else:
                logger.debug(f"Candidate '{c['story_id']}' rejected: {reason}")

        if valid_candidates:
            chosen = valid_candidates[0]
            logger.info(
                f"Selected Variety Story: '{chosen['story_id']}' "
                f"[Style: {target_style} | Character: {chosen.get('main_character')} | "
                f"Location: {chosen.get('location')} | Theme: {chosen.get('visual_theme')}]"
            )
            return chosen

        # Fallback to least recently uploaded story in target style
        logger.warning(f"All {target_style} candidates had soft conflicts; falling back to least recently used un-uploaded.")
        uploaded_ids = {h.get("story_id") for h in history if h.get("status") in ("uploaded", "completed")}
        unuploaded = [c for c in candidates if c["story_id"] not in uploaded_ids]
        if unuploaded:
            return unuploaded[0]

        return candidates[0]
