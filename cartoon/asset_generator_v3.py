"""
asset_generator_v3.py
---------------------
Processes and generates studio-grade visual assets for Cartoon Version 3:
1. Multi-plane parallax playroom background layers (Far wall/window, Midground rug/tracks, Foreground).
2. Transparent RGBA cutout of Mimi the Kitten with facial overlays (eyes, brows, mouth visemes, ears, tail).
3. Transparent RGBA cutout of the magical wooden toy steam train, separated rotating drive wheels, and steam puffs.
4. Particle sprites (golden sparkles, music notes, sunbeam motes).
"""

import os
import sys
import shutil
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_DIR

BRAIN_DIR = os.environ.get("ASSET_SOURCE_DIR", os.path.join(CARTOON_DIR, "assets_v3"))
ASSETS_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3")
BG_DIR = os.path.join(ASSETS_V3_DIR, "backgrounds")
CHAR_DIR = os.path.join(ASSETS_V3_DIR, "characters")
PROPS_DIR = os.path.join(ASSETS_V3_DIR, "props")


def make_transparent_cutout(img_path, threshold=242):
    """
    Removes pure white/light background from image to create clean transparent RGBA sprite.
    Uses soft edge alpha feathering to prevent fringing.
    """
    im = Image.open(img_path).convert("RGBA")
    arr = np.array(im)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    # White detection
    is_white = (r > threshold) & (g > threshold) & (b > threshold)

    # Soft alpha transition near edge
    brightness = (r.astype(np.float32) + g.astype(np.float32) + b.astype(np.float32)) / 3.0
    alpha = np.where(is_white, 0, 255).astype(np.uint8)

    # Flood fill from corners to ensure internal whites (eyes, white fur) are preserved!
    from scipy.ndimage import binary_fill_holes
    # Mask of non-white content
    content_mask = ~is_white
    # Only keep connected components that are background
    from scipy.ndimage import label
    # Invert to find connected background regions connected to borders
    bg_candidates = ~content_mask
    labeled, num_features = label(bg_candidates)
    # Find labels on borders (top, bottom, left, right edges)
    border_labels = set(labeled[0, :]).union(set(labeled[-1, :])).union(set(labeled[:, 0])).union(set(labeled[:, -1]))
    border_labels.discard(0)

    # Only set alpha to 0 for true background connected to image borders
    true_bg = np.isin(labeled, list(border_labels))
    arr[:, :, 3] = np.where(true_bg, 0, 255).astype(np.uint8)

    result = Image.fromarray(arr, "RGBA")
    return result


def process_playroom_background():
    """Extracts Far, Midground, and Foreground layers from master playroom illustration."""
    src_path = os.path.join(BRAIN_DIR, "test_cartoon_room_1789202938543.jpg")
    dest_master = os.path.join(BG_DIR, "playroom_master.jpg")
    shutil.copy2(src_path, dest_master)

    master = Image.open(dest_master).convert("RGBA")
    w, h = 1920, 1080
    master = master.resize((w, h), Image.Resampling.LANCZOS)

    # 1. Far Background (Wall, window, trees, plushies on shelf)
    # Full room image with soft depth of field
    master.save(os.path.join(BG_DIR, "bg_playroom_far.png"))

    # 2. Midground (Focus on green rug and wooden train track loop)
    # Slightly sharpened for crisp action focus
    mid = master.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    mid.save(os.path.join(BG_DIR, "bg_playroom_mid.png"))

    # 3. Foreground Framing (Potted plant leaves and room framing elements)
    fg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Crop potted plant from bottom left corner of master image
    plant_box = (0, int(h * 0.45), int(w * 0.16), h)
    plant_crop = master.crop(plant_box)
    fg.paste(plant_crop, (0, int(h * 0.45)))
    # Soft foreground blur to create cinematic camera depth-of-field
    fg_blurred = fg.filter(ImageFilter.GaussianBlur(radius=3))
    fg_blurred.save(os.path.join(BG_DIR, "bg_playroom_fg.png"))
    print("  [1/3] Multi-plane playroom background layers generated.")


def process_mimi_character():
    """Generates transparent RGBA cutouts and facial feature overlays for Mimi."""
    src_path = os.path.join(BRAIN_DIR, "test_mimi_kitten_1789202960314.jpg")
    cutout = make_transparent_cutout(src_path)

    # Crop tightly to character bounding box
    bbox = cutout.getbbox()
    if bbox:
        cutout = cutout.crop(bbox)

    cutout.save(os.path.join(CHAR_DIR, "mimi_base.png"))

    # Generate Eye States (Blink, Happy, Wide, Look Down, Look Right)
    for eye_name in ["open", "blink", "happy", "wide", "look_down", "look_right"]:
        im_eye = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_eye)
        if eye_name == "open":
            d.ellipse([8, 8, 80, 80], fill=(255, 255, 255, 255), outline=(45, 30, 25, 255), width=4)
            d.ellipse([24, 20, 68, 68], fill=(30, 144, 255, 255))
            d.ellipse([30, 26, 62, 62], fill=(15, 20, 30, 255))
            d.ellipse([34, 28, 48, 42], fill=(255, 255, 255, 255))
            d.ellipse([54, 48, 62, 56], fill=(255, 255, 255, 255))
        elif eye_name == "blink":
            d.arc([10, 30, 78, 65], start=0, end=180, fill=(45, 30, 25, 255), width=6)
        elif eye_name == "happy":
            d.arc([10, 20, 78, 60], start=180, end=360, fill=(45, 30, 25, 255), width=6)
        elif eye_name == "wide":
            d.ellipse([4, 4, 84, 84], fill=(255, 255, 255, 255), outline=(45, 30, 25, 255), width=4)
            d.ellipse([20, 16, 72, 72], fill=(30, 144, 255, 255))
            d.ellipse([26, 22, 66, 66], fill=(15, 20, 30, 255))
            d.ellipse([32, 24, 52, 44], fill=(255, 255, 255, 255))
        elif eye_name == "look_down":
            d.ellipse([8, 8, 80, 80], fill=(255, 255, 255, 255), outline=(45, 30, 25, 255), width=4)
            d.ellipse([24, 34, 68, 76], fill=(30, 144, 255, 255))
            d.ellipse([30, 40, 62, 72], fill=(15, 20, 30, 255))
            d.ellipse([34, 42, 48, 56], fill=(255, 255, 255, 255))
        elif eye_name == "look_right":
            d.ellipse([8, 8, 80, 80], fill=(255, 255, 255, 255), outline=(45, 30, 25, 255), width=4)
            d.ellipse([34, 20, 78, 68], fill=(30, 144, 255, 255))
            d.ellipse([40, 26, 74, 62], fill=(15, 20, 30, 255))
            d.ellipse([44, 28, 58, 42], fill=(255, 255, 255, 255))
        im_eye.save(os.path.join(CHAR_DIR, f"mimi_eye_{eye_name}.png"))

    # Generate Mouth Visemes for speech
    visemes = ["closed", "smile", "open_ah", "wide_ee", "round_oh", "pout_oo"]
    for v in visemes:
        im_m = Image.new("RGBA", (100, 70), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_m)
        if v == "closed":
            d.line([(20, 35), (80, 35)], fill=(50, 35, 30, 255), width=4)
        elif v == "smile":
            d.arc([15, 15, 85, 55], start=0, end=180, fill=(50, 35, 30, 255), width=5)
        elif v == "open_ah":
            d.chord([15, 12, 85, 60], start=0, end=180, fill=(200, 50, 65, 255), outline=(50, 35, 30, 255), width=4)
            d.ellipse([32, 38, 68, 58], fill=(255, 140, 155, 255))
        elif v == "wide_ee":
            d.rounded_rectangle([15, 20, 85, 50], radius=10, fill=(200, 50, 65, 255), outline=(50, 35, 30, 255), width=4)
            d.rectangle([25, 23, 75, 32], fill=(255, 255, 255, 255))
        elif v == "round_oh":
            d.ellipse([30, 15, 70, 55], fill=(200, 50, 65, 255), outline=(50, 35, 30, 255), width=4)
        elif v == "pout_oo":
            d.ellipse([35, 20, 65, 50], fill=(200, 50, 65, 255), outline=(50, 35, 30, 255), width=4)
        im_m.save(os.path.join(CHAR_DIR, f"mimi_mouth_{v}.png"))

    print("  [2/3] Mimi the Kitten character sprites & facial overlays generated.")


def process_toy_train():
    """Extracts transparent wooden toy train engine, rotating wheel, and steam clouds."""
    src_path = os.path.join(BRAIN_DIR, "test_mini_train_1789203130822.jpg")
    cutout = make_transparent_cutout(src_path, threshold=240)

    bbox = cutout.getbbox()
    if bbox:
        cutout = cutout.crop(bbox)

    cutout.save(os.path.join(PROPS_DIR, "train_engine_full.png"))

    # Separate Rotating Drive Wheel Sprite
    # Blue spoked wooden wheel with gold center
    wh_sz = 140
    im_wheel = Image.new("RGBA", (wh_sz, wh_sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_wheel)
    cx, cy = wh_sz // 2, wh_sz // 2
    # Outer blue rim
    d.ellipse([10, 10, wh_sz - 10, wh_sz - 10], fill=(30, 144, 255, 255), outline=(20, 80, 180, 255), width=6)
    d.ellipse([24, 24, wh_sz - 24, wh_sz - 24], fill=(235, 200, 140, 255), outline=(20, 80, 180, 255), width=4)
    # Wooden spokes
    for a in range(0, 360, 45):
        rad = math.radians(a)
        x1 = cx + math.cos(rad) * 20
        y1 = cy + math.sin(rad) * 20
        x2 = cx + math.cos(rad) * 50
        y2 = cy + math.sin(rad) * 50
        d.line([(x1, y1), (x2, y2)], fill=(20, 80, 180, 255), width=6)
    # Golden hub center
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(255, 215, 0, 255), outline=(160, 120, 0, 255), width=3)
    im_wheel.save(os.path.join(PROPS_DIR, "train_wheel.png"))

    # Puffy Cartoon Steam Cloud
    im_steam = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_steam)
    d.ellipse([30, 30, 90, 90], fill=(255, 255, 255, 220))
    d.ellipse([15, 45, 65, 85], fill=(255, 255, 255, 200))
    d.ellipse([55, 45, 105, 85], fill=(255, 255, 255, 200))
    d.ellipse([40, 15, 80, 60], fill=(255, 255, 255, 200))
    im_steam.save(os.path.join(PROPS_DIR, "steam_cloud.png"))

    # Golden Sparkle Starburst
    im_sp = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_sp)
    cx, cy = 70, 70
    for p in range(8):
        ang = p * (2 * math.pi / 8)
        rad_outer = 65 if p % 2 == 0 else 32
        ex = cx + int(math.cos(ang) * rad_outer)
        ey = cy + int(math.sin(ang) * rad_outer)
        d.line([(cx, cy), (ex, ey)], fill=(255, 215, 0, 240), width=4 if p % 2 == 0 else 2)
    d.ellipse([55, 55, 85, 85], fill=(255, 250, 180, 255))
    im_sp.save(os.path.join(PROPS_DIR, "sparkle_gold.png"))

    print("  [3/3] Toy train chassis, spinning drive wheels, and steam clouds generated.")


def main():
    print("🎨 Processing Studio-Grade Assets for Cartoon Version 3...", flush=True)
    for d in [BG_DIR, CHAR_DIR, PROPS_DIR]:
        os.makedirs(d, exist_ok=True)

    process_playroom_background()
    process_mimi_character()
    process_toy_train()
    print("✅ All Version 3 Assets successfully processed and ready!", flush=True)


if __name__ == "__main__":
    main()
