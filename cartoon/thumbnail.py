"""
thumbnail.py
------------
Generates high-CTR, child-friendly YouTube thumbnail (1280x720) for
the cartoon animation episode "Chintu Learns to Share".
Composites high-res characters, background, sparkles, and bold typography.
"""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    WIDTH, HEIGHT, THUMBNAILS_DIR, BACKGROUNDS_DIR,
    PROPS_DIR, CHARACTERS_DIR
)
from cartoon.character_rig import CharacterRig


def get_font(size, bold=True):
    font_candidates = [
        "C:/Windows/Fonts/comicbd.ttf" if bold else "C:/Windows/Fonts/comic.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_cartoon_thumbnail(output_path=None):
    if output_path is None:
        output_path = os.path.join(THUMBNAILS_DIR, "demo_chintu_shares.jpg")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rig = CharacterRig()

    # 1. Base Meadow Background
    bg = Image.open(os.path.join(BACKGROUNDS_DIR, "forest_meadow.png")).convert("RGBA")
    # Crop central vibrant part (1280x720)
    crop_x = (bg.width - WIDTH) // 2
    crop_y = int((bg.height - HEIGHT) * 0.45)
    thumb = bg.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT))

    # 2. Add Oak Tree in background (right side)
    tree = Image.open(os.path.join(BACKGROUNDS_DIR, "oak_tree.png")).convert("RGBA")
    tree_sc = tree.resize((int(tree.width * 0.72), int(tree.height * 0.72)), Image.Resampling.LANCZOS)
    thumb.alpha_composite(tree_sc, (780, 20))

    # 3. Render Chintu (Left side, holding apple half, smiling happily)
    chintu = rig.render_chintu(
        t=1.0, action="hold", eye_state="happy", mouth_state="smile",
        held_item="apple_half_chintu", facing=1, scale=1.02
    )
    thumb.alpha_composite(chintu, (120, 190))

    # 4. Render Golu (Right side, holding apple half, smiling happily)
    golu = rig.render_golu(
        t=1.0, action="receive", eye_state="happy", mouth_state="smile",
        held_item="apple_half_golu", facing=-1, scale=1.06
    )
    thumb.alpha_composite(golu, (690, 180))

    # 5. Golden Sparkles in center
    sparkle = Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA")
    sparkle_positions = [
        (570, 310, 110),
        (510, 240, 75),
        (640, 250, 85),
        (560, 180, 65),
    ]
    for sx, sy, ssz in sparkle_positions:
        sp_sc = sparkle.resize((ssz, ssz), Image.Resampling.LANCZOS)
        thumb.alpha_composite(sp_sc, (sx - ssz // 2, sy - ssz // 2))

    # 6. High-CTR Text Overlays
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_brand = get_font(28, bold=True)
    font_badge = get_font(26, bold=True)
    font_main = get_font(52, bold=True)
    font_sub = get_font(34, bold=True)

    # A. Top Left Brand Badge: "🌟 FUN LEARNING KIDS 🌟"
    b_text = "⭐ FUN LEARNING KIDS ⭐"
    b_bbox = draw.textbbox((0, 0), b_text, font=font_brand)
    bw = b_bbox[2] - b_bbox[0] + 36
    bh = b_bbox[3] - b_bbox[1] + 20
    draw.rounded_rectangle([30, 25, 30 + bw, 25 + bh], radius=14, fill=(255, 179, 0, 240), outline=(255, 255, 255, 255), width=3)
    draw.text((48, 32), b_text, font=font_brand, fill=(30, 30, 30))

    # B. Top Right Tag: "CARTOON STORY 🎬"
    t_text = "CARTOON STORY 🎬"
    t_bbox = draw.textbbox((0, 0), t_text, font=font_badge)
    tw = t_bbox[2] - t_bbox[0] + 32
    th = t_bbox[3] - t_bbox[1] + 18
    tx = WIDTH - tw - 30
    draw.rounded_rectangle([tx, 25, tx + tw, 25 + th], radius=14, fill=(76, 175, 80, 240), outline=(255, 255, 255, 255), width=3)
    draw.text((tx + 16, 31), t_text, font=font_badge, fill=(255, 255, 255))

    # C. Bottom Title Banner
    # Dark transluscent backing for crisp readability
    banner_h = 135
    banner_y = HEIGHT - banner_h - 15
    draw.rounded_rectangle([40, banner_y, WIDTH - 40, banner_y + banner_h], radius=22, fill=(15, 23, 42, 225), outline=(255, 215, 0, 255), width=4)

    # Line 1: Primary Title
    title_1 = "CHINTU & GOLU : SHARING IS CARING! ❤️"
    t1_bbox = draw.textbbox((0, 0), title_1, font=font_main)
    t1_w = t1_bbox[2] - t1_bbox[0]
    t1_x = (WIDTH - t1_w) // 2
    t1_y = banner_y + 12

    # Draw stroked text for maximum pop
    draw.text((t1_x, t1_y), title_1, font=font_main, fill=(255, 235, 59), stroke_width=4, stroke_fill=(10, 10, 10))

    # Line 2: Hindi Subtitle
    title_2 = "चिंटू और गोलू ने सीखा मिल-बाँट कर खाना!"
    t2_bbox = draw.textbbox((0, 0), title_2, font=font_sub)
    t2_w = t2_bbox[2] - t2_bbox[0]
    t2_x = (WIDTH - t2_w) // 2
    t2_y = banner_y + 74

    draw.text((t2_x, t2_y), title_2, font=font_sub, fill=(255, 255, 255), stroke_width=3, stroke_fill=(10, 10, 10))

    # Merge overlay with background
    final_thumb = Image.alpha_composite(thumb, overlay).convert("RGB")
    final_thumb.save(output_path, format="JPEG", quality=95)
    print(f"✅ Cartoon thumbnail created: {output_path} ({os.path.getsize(output_path):,} bytes)")
    return output_path


if __name__ == "__main__":
    create_cartoon_thumbnail()
