"""
thumbnail_v4.py
---------------
Generates high-CTR, child-friendly 1280x720 YouTube thumbnail for
Cartoon Version 4: "Mimi's Magic Toy Train" (मीमी और जादुई रेलगाड़ी).
Featuring Mimi the Kitten, grounded contact shadows, magical steam train,
golden starburst sparkles, channel brand badge, and bold Devanagari typography.
"""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    WIDTH, HEIGHT, THUMBNAILS_DIR, CARTOON_DIR
)
from cartoon.character_rig_v4 import CharacterRigV4

ASSETS_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3")
BG_DIR = os.path.join(ASSETS_V3_DIR, "backgrounds")
PROPS_DIR = os.path.join(ASSETS_V3_DIR, "props")


def get_font(size, bold=True, is_hindi=False):
    if is_hindi:
        if os.path.exists("C:/Windows/Fonts/Nirmala.ttc"):
            try:
                return ImageFont.truetype("C:/Windows/Fonts/Nirmala.ttc", size, index=1 if bold else 0)
            except Exception:
                pass
    candidates = [
        "C:/Windows/Fonts/comicbd.ttf" if bold else "C:/Windows/Fonts/comic.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_star(draw, cx, cy, r_outer, r_inner, fill=(255, 220, 40, 255), outline=(200, 140, 0, 255)):
    points = []
    for i in range(10):
        angle = i * (math.pi / 5) - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=fill, outline=outline)


def create_cartoon_thumbnail_v4(output_path=None):
    if output_path is None:
        output_path = os.path.join(THUMBNAILS_DIR, "demo_v4_mini_train.jpg")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rig = CharacterRigV4()

    # 1. Base Playroom Background (1280x720)
    bg_master = Image.open(os.path.join(BG_DIR, "bg_playroom_mid.png")).convert("RGBA")
    thumb = bg_master.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # 2. Ground Contact Shadows
    # Train contact shadow
    sh_train = rig.render_contact_shadow(290, 70, blur_radius=10, opacity=160)
    thumb.alpha_composite(sh_train, (740 + 130 - sh_train.width // 2, 605 - sh_train.height // 2))

    # Mimi contact shadow
    sh_mimi = rig.render_contact_shadow(240, 65, blur_radius=10, opacity=165)
    thumb.alpha_composite(sh_mimi, (220 + 190 - sh_mimi.width // 2, 665 - sh_mimi.height // 2))

    # 3. Render Toy Train (Right side on floor track, scaled ~0.46)
    train_im = rig.render_toy_train(wheel_rot_deg=35.0, scale=0.46)
    train_x, train_y = 740, 410
    thumb.alpha_composite(train_im, (train_x, train_y))

    # Steam puff from chimney
    steam_im = Image.open(os.path.join(PROPS_DIR, "steam_cloud.png")).convert("RGBA")
    steam_sc = steam_im.resize((140, 140), Image.Resampling.LANCZOS)
    thumb.alpha_composite(steam_sc, (train_x + 60, train_y - 80))

    # 4. Render Mimi the Kitten (Left-center, looking happy, scale ~0.72)
    mimi_im = rig.render_mimi(
        t=1.0,
        acting_state="idle",
        is_speaking=False,
        eye_state="happy",
        mouth_state="smile",
        squash_stretch=(1.02, 0.98),
        tilt_deg=-2.0,
    )
    mw = int(mimi_im.width * 0.72)
    mh = int(mimi_im.height * 0.72)
    mimi_sc = mimi_im.resize((mw, mh), Image.Resampling.LANCZOS)
    thumb.alpha_composite(mimi_sc, (220, 180))

    # 5. Golden Magic Starburst Sparkles around train and Mimi
    sparkle = Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA")
    for sx, sy, ssz, rot in [(720, 360, 120, 15), (960, 340, 100, -25), (630, 220, 80, 45), (320, 140, 95, 30)]:
        sp_r = sparkle.rotate(rot, resample=Image.Resampling.BICUBIC)
        sp_sc = sp_r.resize((ssz, ssz), Image.Resampling.LANCZOS)
        thumb.alpha_composite(sp_sc, (sx - ssz // 2, sy - ssz // 2))

    # 6. Composite Foreground Plant leaves framing bottom-left
    fg = Image.open(os.path.join(BG_DIR, "bg_playroom_fg.png")).convert("RGBA")
    fg_sc = fg.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    thumb.alpha_composite(fg_sc, (0, 0))

    # 7. High-CTR Child-Friendly Typography Overlays
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_brand = get_font(26, bold=True)
    font_main = get_font(56, bold=True)
    font_hindi = get_font(34, bold=True, is_hindi=True)
    font_sub = get_font(28, bold=True)

    # A. Top Left Brand Badge: "FUN LEARNING KIDS" with gold stars
    b_text = "FUN LEARNING KIDS"
    bx, by = 60, 35
    bb = draw.textbbox((bx, by), b_text, font=font_brand)
    pad = 16
    draw.rounded_rectangle(
        [bb[0] - pad - 20, bb[1] - pad // 2, bb[2] + pad + 20, bb[3] + pad // 2],
        radius=14,
        fill=(255, 50, 90, 240),
        outline=(255, 255, 255, 255),
        width=4,
    )
    draw_star(draw, bb[0] - 16, (bb[1] + bb[3]) // 2, 12, 6)
    draw_star(draw, bb[2] + 16, (bb[1] + bb[3]) // 2, 12, 6)
    draw.text((bx, by), b_text, font=font_brand, fill=(255, 255, 255, 255))

    # B. Main Title: "MIMI'S MAGIC TRAIN" in vibrant gold with deep stroke
    main_title = "MIMI'S MAGIC TRAIN"
    tx, ty = 480, 52
    for ox in [-4, -2, 0, 2, 4]:
        for oy in [-4, -2, 0, 2, 4]:
            if ox != 0 or oy != 0:
                draw.text((tx + ox, ty + oy), main_title, font=font_main, fill=(35, 20, 15, 255))
    draw.text((tx, ty), main_title, font=font_main, fill=(255, 230, 40, 255))

    # C. Hindi Title Sub-Badge: "मीमी और जादुई रेलगाड़ी"
    hindi_title = "मीमी और जादुई रेलगाड़ी"
    sx, sy = 560, 128
    sbb = draw.textbbox((sx, sy), hindi_title, font=font_hindi)
    draw.rounded_rectangle(
        [sbb[0] - 20, sbb[1] - 6, sbb[2] + 20, sbb[3] + 8],
        radius=14,
        fill=(30, 130, 235, 240),
        outline=(255, 255, 255, 255),
        width=3,
    )
    draw.text((sx, sy), hindi_title, font=font_hindi, fill=(255, 255, 255, 255))

    # D. Bottom Action Callout Pill: "NEW CARTOON STORY"
    callout = "NEW CARTOON STORY"
    cx, cy = 820, 638
    cbb = draw.textbbox((cx, cy), callout, font=font_sub)
    draw.rounded_rectangle(
        [cbb[0] - 28, cbb[1] - 8, cbb[2] + 28, cbb[3] + 8],
        radius=16,
        fill=(255, 110, 0, 245),
        outline=(255, 255, 255, 255),
        width=4,
    )
    draw_star(draw, cbb[0] - 14, (cbb[1] + cbb[3]) // 2, 10, 5)
    draw_star(draw, cbb[2] + 14, (cbb[1] + cbb[3]) // 2, 10, 5)
    draw.text((cx, cy), callout, font=font_sub, fill=(255, 255, 255, 255))

    thumb.alpha_composite(overlay)
    final_rgb = thumb.convert("RGB")
    final_rgb.save(output_path, "JPEG", quality=95)
    print(f"✅ Cartoon Thumbnail V4 generated: {output_path}", flush=True)
    return output_path


if __name__ == "__main__":
    create_cartoon_thumbnail_v4()
