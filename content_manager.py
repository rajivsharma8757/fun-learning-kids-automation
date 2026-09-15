import os
import sys
import json
import random
import logging
from datetime import datetime
from PIL import Image

from config import (
    BASE_DIR, IMAGE_DIR, TOPICS,
    UPLOADS_HISTORY_FILE, IMAGES_HISTORY_FILE,
    SCRIPTS_HISTORY_FILE, TOPIC_HISTORY_FILE
)
from image_generator import generate_topic_image, compute_file_hash

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

logger = logging.getLogger("kids_automation")

SCRIPTS_BANK_FILE = os.path.join(BASE_DIR, "scripts_bank.json")

def load_json(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class ContentManager:
    def __init__(self):
        self.scripts_bank = load_json(SCRIPTS_BANK_FILE, default={})
        self.images_history = load_json(IMAGES_HISTORY_FILE, default={})
        self.scripts_history = load_json(SCRIPTS_HISTORY_FILE, default={})
        self.topic_history = load_json(TOPIC_HISTORY_FILE, default={"recent": []})
        self._init_images_history()

    def _init_images_history(self):
        """
        Ensures the images history structure is fully populated with rich metadata.
        Maintains backward compatibility for legacy top-level topic lists,
        while storing structured records in the 'details' sub-dictionary.
        """
        if "details" not in self.images_history:
            self.images_history["details"] = {}

        modified = False
        for t in TOPICS:
            used_list = self.images_history.get(t, [])
            for fn in used_list:
                if fn not in self.images_history["details"]:
                    file_path = os.path.join(IMAGE_DIR, t, fn)
                    file_hash = compute_file_hash(file_path) if os.path.exists(file_path) else None
                    self.images_history["details"][fn] = {
                        "filename": fn,
                        "topic": t,
                        "first_used": "2026-09-11 00:00:00",
                        "last_used": "2026-09-12 00:00:00",
                        "usage_count": 1,
                        "is_generated": fn.startswith("generated_"),
                        "generated_at": None,
                        "file_hash": file_hash
                    }
                    modified = True

        if modified:
            save_json(IMAGES_HISTORY_FILE, self.images_history)

    def _is_valid_image(self, filepath):
        """Verifies that the image file exists, is non-empty, and can be read by Pillow."""
        try:
            if not os.path.isfile(filepath):
                return False
            if os.path.getsize(filepath) < 1000:
                logger.warning(f"Image too small/empty: {filepath}")
                return False
            with Image.open(filepath) as img:
                img.verify()
            return True
        except Exception as e:
            logger.warning(f"Skipping corrupted or unreadable image {filepath}: {e}")
            return False

    def get_next_topic(self, requested_topic=None, slot=None):
        """
        Chooses the next topic intelligently.
        Ensures 2 videos per day (e.g. morning and evening) use different topics,
        and cycles fairly through all 5 topics.
        """
        if requested_topic and requested_topic in TOPICS:
            return requested_topic

        recent = self.topic_history.get("recent", [])
        
        # If there's a recent topic today from the earlier slot, don't repeat it
        available = [t for t in TOPICS if not recent or t != recent[-1]]
        if not available:
            available = TOPICS

        # Pick least recently used topic
        usage_counts = {t: recent.count(t) for t in available}
        min_count = min(usage_counts.values())
        candidates = [t for t, count in usage_counts.items() if count == min_count]
        chosen = random.choice(candidates)

        # Update history
        recent.append(chosen)
        if len(recent) > 20:
            recent = recent[-20:]
        self.topic_history["recent"] = recent
        save_json(TOPIC_HISTORY_FILE, self.topic_history)

        return chosen

    def get_next_script(self, topic):
        """
        Selects an unused script for the given topic.
        Resets tracking when all scripts in this topic have been used once.
        """
        topic_scripts = self.scripts_bank.get(topic, [])
        if not topic_scripts:
            raise ValueError(f"No scripts found in scripts_bank.json for topic: {topic}")

        used_ids = set(self.scripts_history.get(topic, []))
        available = [s for s in topic_scripts if s["id"] not in used_ids]

        if not available:
            # All scripts used! Reset the cycle for this topic
            available = topic_scripts
            used_ids = set()

        chosen_script = random.choice(available)

        # Record usage
        used_ids.add(chosen_script["id"])
        self.scripts_history[topic] = list(used_ids)
        save_json(SCRIPTS_HISTORY_FILE, self.scripts_history)

        return chosen_script

    def get_topic_images(self, topic, count=1, script=None):
        """
        Selects topic images while prioritizing unused existing library images.
        Tracks detailed usage metadata in history/images_used.json.
        When existing images for a topic are exhausted, automatically generates
        a new original child-safe cartoon image, validates it, adds it to the
        library and history, and returns it.
        """
        topic_folder = os.path.join(IMAGE_DIR, topic)
        if not os.path.exists(topic_folder):
            raise FileNotFoundError(f"Topic image folder not found: {topic_folder}")

        valid_exts = (".jpg", ".jpeg", ".png", ".webp")
        candidate_files = [
            f for f in os.listdir(topic_folder)
            if f.lower().endswith(valid_exts)
        ]

        # Filter out any corrupted or unreadable image files safely
        all_valid_images = [
            f for f in candidate_files
            if self._is_valid_image(os.path.join(topic_folder, f))
        ]

        used_list = self.images_history.setdefault(topic, [])
        details = self.images_history.setdefault("details", {})

        # Unused images are valid candidate files that have not yet been used
        unused_images = [img for img in all_valid_images if img not in used_list]

        if len(unused_images) >= count:
            # 1. Unused existing images are available: USE THEM FIRST
            chosen = random.sample(unused_images, count)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for img in chosen:
                used_list.append(img)
                rec = details.get(img, {})
                file_path = os.path.join(topic_folder, img)
                file_hash = rec.get("file_hash") or compute_file_hash(file_path)

                details[img] = {
                    "filename": img,
                    "topic": topic,
                    "first_used": rec.get("first_used") or now_str,
                    "last_used": now_str,
                    "usage_count": rec.get("usage_count", 0) + 1,
                    "is_generated": rec.get("is_generated", img.startswith("generated_")),
                    "generated_at": rec.get("generated_at"),
                    "file_hash": file_hash
                }

            self.images_history[topic] = used_list
            save_json(IMAGES_HISTORY_FILE, self.images_history)

            logger.info(f"🖼️ Selected unused library image(s) for '{topic}': {chosen} ({len(unused_images) - count} unused remain)")
            return [os.path.join(topic_folder, img) for img in chosen]

        # 2. Existing image library for this topic is EXHAUSTED!
        logger.warning(f"⚠️ Image library for topic '{topic}' is EXHAUSTED! All {len(all_valid_images)} existing images have been used.")
        logger.info(f"🎨 Triggering automatic new image generation for topic '{topic}'...")

        # Collect all known hashes to guarantee duplicate protection
        known_hashes = {
            rec.get("file_hash") for rec in details.values() if rec.get("file_hash")
        }

        gen_path, gen_fn, gen_hash = generate_topic_image(
            topic=topic,
            script=script,
            known_hashes=known_hashes
        )

        if not gen_path or not os.path.exists(gen_path):
            logger.error(f"❌ Automatic image generation failed for topic '{topic}'. Video pipeline stopped safely.")
            raise RuntimeError(f"Failed to generate valid new image for topic '{topic}'. Video task left pending.")

        # Record newly generated image in library and history
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        used_list.append(gen_fn)
        self.images_history[topic] = used_list

        details[gen_fn] = {
            "filename": gen_fn,
            "topic": topic,
            "first_used": now_str,
            "last_used": now_str,
            "usage_count": 1,
            "is_generated": True,
            "generated_at": now_str,
            "file_hash": gen_hash
        }

        save_json(IMAGES_HISTORY_FILE, self.images_history)
        logger.info(f"✨ New image '{gen_fn}' added to permanent library and history for '{topic}'. Returning for video generation.")

        return [gen_path]

    def get_image_stats(self):
        """Returns statistics on the image library and usage per topic."""
        stats = {}
        total_all = 0
        used_all = 0
        unused_all = 0
        gen_all = 0

        valid_exts = (".jpg", ".jpeg", ".png", ".webp")

        for t in TOPICS:
            p = os.path.join(IMAGE_DIR, t)
            if not os.path.exists(p):
                continue
            files = [f for f in os.listdir(p) if f.lower().endswith(valid_exts)]
            used_list = self.images_history.get(t, [])
            unused_list = [f for f in files if f not in used_list]
            generated_list = [f for f in files if f.startswith("generated_")]

            stats[t] = {
                "total": len(files),
                "used": len(used_list),
                "unused": len(unused_list),
                "generated": len(generated_list)
            }
            total_all += len(files)
            used_all += len(used_list)
            unused_all += len(unused_list)
            gen_all += len(generated_list)

        stats["_total"] = {
            "total": total_all,
            "used": used_all,
            "unused": unused_all,
            "generated": gen_all
        }
        return stats

if __name__ == "__main__":
    cm = ContentManager()
    t = cm.get_next_topic()
    s = cm.get_next_script(t)
    imgs = cm.get_topic_images(t, count=1, script=s)
    print("Test Topic:", t)
    print("Test Script Title:", s["title"])
    print("Test Image:", imgs[0])
    print("Image Stats:", json.dumps(cm.get_image_stats(), indent=2))
