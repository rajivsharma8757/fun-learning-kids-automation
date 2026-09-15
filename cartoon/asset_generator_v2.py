"""
asset_generator_v2.py
---------------------
Generates professional high-resolution vector/cel-shaded assets for Cartoon Version 2:
1. 18 Background Layers (6 distinct scenes x 3 parallax depth layers: Sky, Midground, Foreground).
2. Fully Articulated Character Rigs (Chintu Bunny & Golu Bear modular parts:
   head, torso, ears, scarf, upper/lower arms, upper/lower legs, eyes, brows, visemes).
3. Interactive Props: whole apple, split halves, bitten halves, butterfly frames,
   dandelion puffs, leaves, sparkles, sunbeams, musical notes.
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    ASSETS_DIR, BACKGROUNDS_DIR, CHARACTERS_DIR, PROPS_DIR
)


def ensure_dirs():
    for d in [BACKGROUNDS_DIR, CHARACTERS_DIR, PROPS_DIR]:
        os.makedirs(d, exist_ok=True)


# =====================================================================
# 1. SIX DISTINCT MULTI-LAYER PARALLAX BACKGROUNDS (1920x1080)
# =====================================================================

BG_W = 1920
BG_H = 1080


def create_gradient_canvas(w, h, top_color, bottom_color):
    """Creates smooth vertical gradient image."""
    base = Image.new("RGBA", (w, h))
    top_r, top_g, top_b = top_color
    bot_r, bot_g, bot_b = bottom_color
    data = []
    for y in range(h):
        ratio = y / float(h)
        r = int(top_r + (bot_r - top_r) * ratio)
        g = int(top_g + (bot_g - top_g) * ratio)
        b = int(bot_b + (bot_b - top_b) * ratio)
        data.extend([(r, g, b, 255)] * w)
    base.putdata(data)
    return base


def draw_fluffy_cloud(draw, cx, cy, scale=1.0, alpha=235):
    col = (255, 255, 255, alpha)
    sh_col = (220, 235, 245, alpha)
    # Cloud base shadow
    draw.ellipse([cx - int(70 * scale), cy - int(10 * scale), cx + int(70 * scale), cy + int(35 * scale)], fill=sh_col)
    # Cloud puffs
    draw.ellipse([cx - int(60 * scale), cy - int(25 * scale), cx - int(10 * scale), cy + int(25 * scale)], fill=col)
    draw.ellipse([cx - int(25 * scale), cy - int(45 * scale), cx + int(35 * scale), cy + int(25 * scale)], fill=col)
    draw.ellipse([cx + int(10 * scale), cy - int(30 * scale), cx + int(65 * scale), cy + int(25 * scale)], fill=col)
    draw.ellipse([cx - int(50 * scale), cy - int(15 * scale), cx + int(50 * scale), cy + int(25 * scale)], fill=col)


def generate_scene1_forest_meadow():
    """Scene 1: Forest Meadow Edge - Hook (Sunny morning, rolling hills, distant trees)"""
    # 1. Sky Layer
    sky = create_gradient_canvas(BG_W, BG_H, (120, 195, 245), (215, 240, 255))
    s_draw = ImageDraw.Draw(sky)
    draw_fluffy_cloud(s_draw, 300, 180, 1.2)
    draw_fluffy_cloud(s_draw, 850, 130, 0.9)
    draw_fluffy_cloud(s_draw, 1450, 200, 1.4)
    # Distant mountains
    s_draw.polygon([(0, 680), (380, 480), (750, 680)], fill=(160, 195, 215, 220))
    s_draw.polygon([(650, 680), (1050, 440), (1480, 680)], fill=(150, 185, 210, 220))
    s_draw.polygon([(1350, 680), (1700, 500), (1920, 680)], fill=(160, 195, 215, 220))
    sky.save(os.path.join(BACKGROUNDS_DIR, "scene1_sky.png"))

    # 2. Midground Layer (Rolling green hills & trees)
    mid = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mid)
    # Back hill
    m_draw.chord([ -150, 520, 1150, 1200], start=0, end=360, fill=(106, 190, 85, 255))
    # Mid hill
    m_draw.chord([ 750, 480, 2150, 1220], start=0, end=360, fill=(90, 175, 70, 255))
    # Main meadow hill
    m_draw.chord([ 100, 560, 1850, 1300], start=0, end=360, fill=(120, 205, 95, 255))
    # Stylized background bushes & trees
    for bx, by, br in [(220, 570, 45), (270, 550, 55), (330, 565, 40), (1600, 530, 50), (1660, 510, 65), (1730, 525, 45)]:
        m_draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(65, 145, 55, 255))
    # Colorful wild flowers on hill
    for fx, fy, fcol in [(400, 720, (255, 105, 180)), (520, 750, (255, 235, 59)), (680, 710, (255, 255, 255)),
                        (1100, 740, (255, 215, 0)), (1280, 715, (255, 105, 180)), (1450, 735, (255, 255, 255))]:
        m_draw.ellipse([fx - 8, fy - 8, fx + 8, fy + 8], fill=(*fcol, 255))
        m_draw.ellipse([fx - 4, fy - 4, fx + 4, fy + 4], fill=(255, 165, 0, 255))
    mid.save(os.path.join(BACKGROUNDS_DIR, "scene1_mid.png"))

    # 3. Foreground Layer (Lush grass blades & framing)
    fg = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fg)
    for x in range(0, BG_W, 18):
        gh = 55 + (x * 7) % 35
        curve = ((x % 36) - 18)
        f_draw.polygon([(x, BG_H), (x + 8, BG_H), (x + 4 + curve, BG_H - gh)], fill=(45, 120, 35, 255))
    fg.save(os.path.join(BACKGROUNDS_DIR, "scene1_fg.png"))


def generate_scene2_the_great_tree():
    """Scene 2: The Great Oak Tree - Discovery (Massive tree, juicy apples, grassy knoll)"""
    # 1. Sky
    sky = create_gradient_canvas(BG_W, BG_H, (110, 190, 245), (210, 238, 255))
    s_draw = ImageDraw.Draw(sky)
    draw_fluffy_cloud(s_draw, 400, 150, 1.1)
    draw_fluffy_cloud(s_draw, 1100, 180, 1.3)
    sky.save(os.path.join(BACKGROUNDS_DIR, "scene2_sky.png"))

    # 2. Midground (Massive Oak Tree taking right side of frame, boughs with apples)
    mid = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mid)
    # Rolling grassy ground
    m_draw.chord([-100, 520, 2050, 1300], start=0, end=360, fill=(115, 200, 90, 255))
    # Massive Tree Trunk (curving up right side)
    m_draw.polygon([(1450, 1080), (1380, 680), (1420, 380), (1600, 380), (1680, 680), (1750, 1080)], fill=(120, 75, 45, 255))
    # Tree Roots
    m_draw.polygon([(1380, 780), (1220, 880), (1240, 920), (1420, 850)], fill=(105, 65, 38, 255))
    m_draw.polygon([(1650, 790), (1820, 910), (1840, 870), (1680, 780)], fill=(105, 65, 38, 255))
    # Giant Foliage Canopy
    canopy_clusters = [
        (1480, 280, 260), (1280, 310, 210), (1680, 290, 220),
        (1380, 160, 240), (1580, 150, 250), (1150, 390, 180)
    ]
    for cx, cy, cr in canopy_clusters:
        m_draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(55, 145, 45, 255))
    for cx, cy, cr in [(1440, 250, 230), (1320, 280, 180), (1560, 240, 200), (1380, 130, 200)]:
        m_draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(75, 175, 60, 255))
    # Apples hanging in tree boughs
    tree_apples = [(1250, 350), (1350, 270), (1480, 380), (1620, 310), (1200, 420), (1410, 450)]
    for ax, ay in tree_apples:
        m_draw.ellipse([ax - 16, ay - 16, ax + 16, ay + 16], fill=(230, 45, 55, 255))
        m_draw.ellipse([ax - 10, ay - 12, ax - 4, ay - 6], fill=(255, 140, 150, 255))  # highlight
        m_draw.line([(ax, ay - 16), (ax + 4, ay - 24)], fill=(80, 50, 30, 255), width=3)
    mid.save(os.path.join(BACKGROUNDS_DIR, "scene2_mid.png"))

    # 3. Foreground (Fallen leaves, mossy ground detail)
    fg = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fg)
    for x in range(0, BG_W, 20):
        gh = 45 + (x * 11) % 30
        f_draw.polygon([(x, BG_H), (x + 8, BG_H), (x + 4, BG_H - gh)], fill=(40, 115, 30, 255))
    fg.save(os.path.join(BACKGROUNDS_DIR, "scene2_fg.png"))


def generate_scene3_woodland_path():
    """Scene 3: Woodland Trail - Conflict (Curved dirt trail, birch trees, berry bushes)"""
    # 1. Sky
    sky = create_gradient_canvas(BG_W, BG_H, (135, 205, 250), (225, 245, 255))
    s_draw = ImageDraw.Draw(sky)
    draw_fluffy_cloud(s_draw, 700, 160, 1.0)
    sky.save(os.path.join(BACKGROUNDS_DIR, "scene3_sky.png"))

    # 2. Midground (Curved dirt path winding from right to left)
    mid = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mid)
    # Grassy embankment
    m_draw.rectangle([0, 480, BG_W, BG_H], fill=(95, 180, 75, 255))
    # Winding dirt trail
    path_pts = [
        (1920, 680), (1450, 710), (1050, 740), (600, 780), (0, 840),
        (0, 1080), (1920, 1080)
    ]
    m_draw.polygon(path_pts, fill=(215, 175, 125, 255))
    # Trail pebbles & texture
    for px, py in [(800, 820), (1100, 780), (1350, 750), (1550, 725), (650, 860), (450, 910)]:
        m_draw.ellipse([px - 10, py - 6, px + 10, py + 6], fill=(185, 145, 100, 255))
    # Background birch trees
    for tx in [200, 450, 1650, 1820]:
        m_draw.polygon([(tx, 1080), (tx + 10, 420), (tx + 45, 420), (tx + 55, 1080)], fill=(245, 245, 240, 255))
        # Birch bark dark notches
        for ny in range(480, 950, 60):
            m_draw.line([(tx + 5, ny), (tx + 25, ny - 5)], fill=(60, 60, 60, 255), width=4)
    # Berry bushes along the path
    for bx, by in [(350, 640), (750, 610), (1500, 580)]:
        m_draw.ellipse([bx - 60, by - 40, bx + 60, by + 40], fill=(50, 135, 45, 255))
        for ox, oy in [(-25, 5), (0, -10), (20, 10), (-10, 15), (25, -8)]:
            m_draw.ellipse([bx + ox - 6, by + oy - 6, bx + ox + 6, by + oy + 6], fill=(180, 30, 65, 255))
    mid.save(os.path.join(BACKGROUNDS_DIR, "scene3_mid.png"))

    # 3. Foreground (Overhanging foliage in top corners for depth framing)
    fg = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fg)
    # Top left hanging leaves
    for lx, ly, lr in [(80, 60, 110), (200, 40, 90), (0, 140, 120), (120, 160, 80)]:
        f_draw.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=(45, 115, 35, 240))
    # Bottom grass edge
    for x in range(0, BG_W, 22):
        gh = 40 + (x * 13) % 25
        f_draw.polygon([(x, BG_H), (x + 8, BG_H), (x + 4, BG_H - gh)], fill=(35, 105, 25, 255))
    fg.save(os.path.join(BACKGROUNDS_DIR, "scene3_fg.png"))


def generate_scene4_sunlit_clearing():
    """Scene 4: Sunlit Clearing - The WOW Moment (Intimate warm clearing, flowers, sunbeam)"""
    # 1. Sky
    sky = create_gradient_canvas(BG_W, BG_H, (95, 185, 245), (205, 238, 255))
    s_draw = ImageDraw.Draw(sky)
    draw_fluffy_cloud(s_draw, 500, 140, 1.3)
    draw_fluffy_cloud(s_draw, 1350, 160, 1.2)
    sky.save(os.path.join(BACKGROUNDS_DIR, "scene4_sky.png"))

    # 2. Midground (Lush sun-drenched clearing with flower carpet and gentle hill)
    mid = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mid)
    # Deep rolling hills
    m_draw.chord([-200, 450, 1400, 1250], start=0, end=360, fill=(95, 185, 75, 255))
    m_draw.chord([600, 430, 2200, 1250], start=0, end=360, fill=(110, 200, 85, 255))
    m_draw.chord([100, 520, 1850, 1350], start=0, end=360, fill=(130, 215, 100, 255))
    # Beautiful flower patches
    for fx, fy, col in [
        (350, 710, (255, 182, 193)), (480, 750, (255, 255, 255)), (620, 730, (255, 215, 0)),
        (850, 700, (147, 112, 219)), (1050, 720, (255, 105, 180)), (1300, 740, (255, 255, 255)),
        (1500, 710, (255, 215, 0))
    ]:
        for p in range(5):
            angle = p * (2 * math.pi / 5)
            px = fx + int(math.cos(angle) * 12)
            py = fy + int(math.sin(angle) * 12)
            m_draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(*col, 255))
        m_draw.ellipse([fx - 5, fy - 5, fx + 5, fy + 5], fill=(255, 165, 0, 255))
    mid.save(os.path.join(BACKGROUNDS_DIR, "scene4_mid.png"))

    # 3. Foreground (Sunlit soft blades of grass & dandelion seed heads)
    fg = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fg)
    for x in range(0, BG_W, 16):
        gh = 50 + (x * 9) % 35
        f_draw.polygon([(x, BG_H), (x + 8, BG_H), (x + 4, BG_H - gh)], fill=(50, 130, 40, 255))
    fg.save(os.path.join(BACKGROUNDS_DIR, "scene4_fg.png"))


def generate_scene5_picnic_glade():
    """Scene 5: Playful Picnic Glade - Celebration (Mossy log bench, joyful woodland spot)"""
    # 1. Sky
    sky = create_gradient_canvas(BG_W, BG_H, (100, 190, 245), (210, 240, 255))
    s_draw = ImageDraw.Draw(sky)
    draw_fluffy_cloud(s_draw, 600, 140, 1.2)
    draw_fluffy_cloud(s_draw, 1400, 170, 1.1)
    sky.save(os.path.join(BACKGROUNDS_DIR, "scene5_sky.png"))

    # 2. Midground (Glade with smooth fallen log bench in background)
    mid = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mid)
    # Meadow base
    m_draw.chord([-100, 500, 2020, 1300], start=0, end=360, fill=(125, 210, 95, 255))
    # Mossy wooden log bench
    m_draw.rounded_rectangle([420, 680, 1500, 750], radius=25, fill=(110, 70, 40, 255))
    # Moss patches on log
    for mx in [500, 720, 950, 1200, 1380]:
        m_draw.ellipse([mx - 40, 670, mx + 40, 700], fill=(75, 160, 60, 255))
    # Background celebration flower borders
    for bx in range(200, 1800, 140):
        m_draw.ellipse([bx - 20, 580, bx + 20, 620], fill=(55, 145, 45, 255))
        m_draw.ellipse([bx - 8, 570, bx + 8, 586], fill=(255, 215, 0, 255))
    mid.save(os.path.join(BACKGROUNDS_DIR, "scene5_mid.png"))

    # 3. Foreground (Grass & clover)
    fg = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fg)
    for x in range(0, BG_W, 20):
        gh = 45 + (x * 11) % 30
        f_draw.polygon([(x, BG_H), (x + 8, BG_H), (x + 4, BG_H - gh)], fill=(45, 120, 35, 255))
    fg.save(os.path.join(BACKGROUNDS_DIR, "scene5_fg.png"))


def generate_scene6_sunset_outlook():
    """Scene 6: Golden Sunset Outlook - Moral & Outro (Warm sunset sky, glowing horizon, rim light)"""
    # 1. Sky (Warm sunset gradient: deep twilight lavender -> amber orange -> golden yellow)
    sky = create_gradient_canvas(BG_W, BG_H, (180, 100, 180), (255, 180, 60))
    s_draw = ImageDraw.Draw(sky)
    # Giant glowing golden sun setting on horizon
    sun_x, sun_y = 960, 650
    for r in range(240, 40, -30):
        alpha = int(50 * (1.0 - r / 260.0))
        s_draw.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=(255, 235, 120, alpha))
    s_draw.ellipse([sun_x - 85, sun_y - 85, sun_x + 85, sun_y + 85], fill=(255, 245, 180, 240))
    # Soft sunset clouds
    draw_fluffy_cloud(s_draw, 350, 240, 1.3, alpha=180)
    draw_fluffy_cloud(s_draw, 1480, 220, 1.4, alpha=180)
    sky.save(os.path.join(BACKGROUNDS_DIR, "scene6_sky.png"))

    # 2. Midground (Golden sunset hills with warm silhouettes)
    mid = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mid)
    # Distant sunset ridge
    m_draw.chord([-150, 520, 1250, 1250], start=0, end=360, fill=(185, 95, 60, 255))
    m_draw.chord([650, 500, 2150, 1250], start=0, end=360, fill=(165, 80, 50, 255))
    # Main foreground hill in warm golden amber
    m_draw.chord([100, 580, 1850, 1350], start=0, end=360, fill=(145, 70, 45, 255))
    # Distant pine tree silhouettes
    for px in [150, 220, 310, 1580, 1680, 1790]:
        m_draw.polygon([(px, 620), (px + 20, 480), (px + 40, 620)], fill=(75, 35, 30, 255))
    mid.save(os.path.join(BACKGROUNDS_DIR, "scene6_mid.png"))

    # 3. Foreground (Warm twilight grass)
    fg = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(fg)
    for x in range(0, BG_W, 18):
        gh = 55 + (x * 15) % 35
        f_draw.polygon([(x, BG_H), (x + 8, BG_H), (x + 4, BG_H - gh)], fill=(65, 28, 25, 255))
    fg.save(os.path.join(BACKGROUNDS_DIR, "scene6_fg.png"))


# =====================================================================
# 2. MODULAR ARTICULATED CHARACTER RIG ASSETS
# =====================================================================

def generate_chintu_bunny_parts():
    """Generates high-res modular components for Chintu Bunny."""
    # 1. Head (with cute cheeks, pink nose, whiskers, mouth socket)
    im_head = Image.new("RGBA", (340, 320), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_head)
    # Head outline & fill (soft warm white)
    d.ellipse([40, 30, 300, 270], fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=4)
    # Rosy Cheeks
    d.ellipse([55, 175, 115, 220], fill=(255, 175, 195, 180))
    d.ellipse([225, 175, 285, 220], fill=(255, 175, 195, 180))
    # Cute Pink Nose
    d.polygon([(155, 168), (185, 168), (170, 184)], fill=(255, 125, 160, 255), outline=(60, 45, 45, 255))
    # Whiskers
    d.line([(60, 180), (120, 185)], fill=(80, 70, 70, 200), width=2)
    d.line([(55, 198), (115, 196)], fill=(80, 70, 70, 200), width=2)
    d.line([(280, 180), (220, 185)], fill=(80, 70, 70, 200), width=2)
    d.line([(285, 198), (225, 196)], fill=(80, 70, 70, 200), width=2)
    im_head.save(os.path.join(CHARACTERS_DIR, "chintu_head.png"))

    # 2. Torso with Teal Overalls & Gold Buttons
    im_torso = Image.new("RGBA", (260, 280), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_torso)
    # Base fluffy body
    d.ellipse([45, 40, 215, 240], fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=4)
    # Teal Overalls pants/body
    d.chord([45, 90, 215, 250], start=0, end=360, fill=(0, 168, 150, 255), outline=(30, 45, 45, 255), width=3)
    # Overalls Straps
    d.polygon([(65, 45), (95, 45), (85, 150), (55, 150)], fill=(0, 140, 125, 255), outline=(30, 45, 45, 255), width=2)
    d.polygon([(195, 45), (165, 45), (175, 150), (205, 150)], fill=(0, 140, 125, 255), outline=(30, 45, 45, 255), width=2)
    # Golden Buttons
    d.ellipse([70, 125, 88, 143], fill=(255, 215, 0, 255), outline=(150, 100, 0, 255), width=2)
    d.ellipse([172, 125, 190, 143], fill=(255, 215, 0, 255), outline=(150, 100, 0, 255), width=2)
    # Front Pocket
    d.rounded_rectangle([105, 155, 155, 195], radius=6, fill=(0, 145, 130, 255), outline=(20, 45, 45, 255), width=2)
    im_torso.save(os.path.join(CHARACTERS_DIR, "chintu_torso.png"))

    # 3. Ears (Long floppy ears with soft pink inner cushion)
    for side in ["l", "r"]:
        im_ear = Image.new("RGBA", (100, 220), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_ear)
        # Outer ear
        d.ellipse([15, 10, 85, 210], fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=4)
        # Inner ear pink
        d.ellipse([30, 35, 70, 185], fill=(255, 185, 205, 255))
        im_ear.save(os.path.join(CHARACTERS_DIR, f"chintu_ear_{side}.png"))

    # 4. Upper Arm & Lower Arm (Hand/Paw)
    im_uarm = Image.new("RGBA", (65, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_uarm)
    d.rounded_rectangle([12, 10, 52, 100], radius=18, fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=3)
    im_uarm.save(os.path.join(CHARACTERS_DIR, "chintu_arm_upper.png"))

    im_larm = Image.new("RGBA", (70, 115), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_larm)
    d.rounded_rectangle([12, 10, 56, 75], radius=16, fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=3)
    # Rounded Paw Hand
    d.ellipse([10, 55, 60, 105], fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=3)
    im_larm.save(os.path.join(CHARACTERS_DIR, "chintu_arm_lower.png"))

    # 5. Upper Leg & Lower Leg (Foot with pink pad)
    im_uleg = Image.new("RGBA", (70, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_uleg)
    d.rounded_rectangle([12, 10, 58, 100], radius=18, fill=(0, 150, 135, 255), outline=(30, 45, 45, 255), width=3)
    im_uleg.save(os.path.join(CHARACTERS_DIR, "chintu_leg_upper.png"))

    im_lleg = Image.new("RGBA", (85, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_lleg)
    # Lower leg
    d.rounded_rectangle([20, 10, 65, 75], radius=16, fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=3)
    # Big bunny foot
    d.ellipse([10, 55, 80, 112], fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=3)
    # Pink paw pad
    d.ellipse([25, 72, 65, 102], fill=(255, 185, 205, 220))
    im_lleg.save(os.path.join(CHARACTERS_DIR, "chintu_leg_lower.png"))

    # 6. Fluffy Tail
    im_tail = Image.new("RGBA", (70, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_tail)
    d.ellipse([10, 10, 60, 60], fill=(250, 250, 252, 255), outline=(50, 45, 45, 255), width=3)
    im_tail.save(os.path.join(CHARACTERS_DIR, "chintu_tail.png"))

    # 7. Eyes (6 expressive states)
    for state in ["open", "blink", "happy", "wide", "look_down", "look_right"]:
        im_eye = Image.new("RGBA", (65, 65), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_eye)
        if state == "open":
            d.ellipse([8, 8, 56, 56], fill=(255, 255, 255, 255), outline=(40, 35, 35, 255), width=3)
            d.ellipse([20, 16, 48, 48], fill=(60, 90, 160, 255))  # iris
            d.ellipse([25, 20, 43, 44], fill=(20, 20, 25, 255))   # pupil
            d.ellipse([30, 22, 38, 30], fill=(255, 255, 255, 255))# specular catchlight
        elif state == "blink":
            d.arc([10, 20, 54, 45], start=0, end=180, fill=(40, 35, 35, 255), width=4)
        elif state == "happy":
            d.arc([10, 14, 54, 44], start=180, end=360, fill=(40, 35, 35, 255), width=4)
        elif state == "wide":
            d.ellipse([4, 4, 60, 60], fill=(255, 255, 255, 255), outline=(40, 35, 35, 255), width=3)
            d.ellipse([18, 14, 50, 50], fill=(60, 90, 160, 255))
            d.ellipse([22, 18, 46, 46], fill=(20, 20, 25, 255))
            d.ellipse([28, 20, 40, 32], fill=(255, 255, 255, 255))
        elif state == "look_down":
            d.ellipse([8, 8, 56, 56], fill=(255, 255, 255, 255), outline=(40, 35, 35, 255), width=3)
            d.ellipse([20, 26, 48, 54], fill=(60, 90, 160, 255))
            d.ellipse([24, 30, 44, 52], fill=(20, 20, 25, 255))
            d.ellipse([28, 32, 36, 40], fill=(255, 255, 255, 255))
        elif state == "look_right":
            d.ellipse([8, 8, 56, 56], fill=(255, 255, 255, 255), outline=(40, 35, 35, 255), width=3)
            d.ellipse([28, 16, 54, 48], fill=(60, 90, 160, 255))
            d.ellipse([32, 20, 50, 44], fill=(20, 20, 25, 255))
            d.ellipse([36, 22, 44, 30], fill=(255, 255, 255, 255))
        im_eye.save(os.path.join(CHARACTERS_DIR, f"chintu_eye_{state}.png"))

    # 8. Eyebrows
    for b_state in ["neutral", "happy", "curious", "surprised"]:
        im_b = Image.new("RGBA", (60, 35), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_b)
        if b_state == "neutral":
            d.line([(8, 18), (52, 18)], fill=(60, 50, 50, 255), width=4)
        elif b_state == "happy":
            d.arc([8, 6, 52, 30], start=180, end=360, fill=(60, 50, 50, 255), width=4)
        elif b_state == "curious":
            d.line([(8, 22), (52, 10)], fill=(60, 50, 50, 255), width=4)
        elif b_state == "surprised":
            d.arc([8, 2, 52, 22], start=180, end=360, fill=(60, 50, 50, 255), width=4)
        im_b.save(os.path.join(CHARACTERS_DIR, f"chintu_brow_{b_state}.png"))

    # 9. Mouth Visemes (7 states for speech cadence)
    visemes = ["closed", "smile", "open_ah", "wide_ee", "round_oh", "pout_oo", "munch_crunch"]
    for v in visemes:
        im_m = Image.new("RGBA", (75, 55), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_m)
        if v == "closed":
            d.line([(15, 26), (60, 26)], fill=(50, 35, 35, 255), width=3)
        elif v == "smile":
            d.arc([15, 12, 60, 36], start=0, end=180, fill=(50, 35, 35, 255), width=4)
        elif v == "open_ah":
            d.chord([15, 10, 60, 46], start=0, end=180, fill=(180, 45, 55, 255), outline=(50, 35, 35, 255), width=3)
            d.ellipse([24, 28, 51, 44], fill=(255, 130, 140, 255))  # tongue
        elif v == "wide_ee":
            d.rounded_rectangle([10, 16, 65, 36], radius=8, fill=(180, 45, 55, 255), outline=(50, 35, 35, 255), width=3)
            d.rectangle([18, 18, 57, 24], fill=(255, 255, 255, 255))  # teeth
        elif v == "round_oh":
            d.ellipse([22, 10, 53, 44], fill=(180, 45, 55, 255), outline=(50, 35, 35, 255), width=3)
        elif v == "pout_oo":
            d.ellipse([26, 16, 48, 38], fill=(180, 45, 55, 255), outline=(50, 35, 35, 255), width=3)
        elif v == "munch_crunch":
            d.polygon([(18, 25), (30, 15), (45, 28), (56, 18), (48, 34), (25, 32)], fill=(180, 45, 55, 255), outline=(50, 35, 35, 255), width=3)
        im_m.save(os.path.join(CHARACTERS_DIR, f"chintu_mouth_{v}.png"))


def generate_golu_bear_parts():
    """Generates high-res modular components for Golu Bear."""
    # 1. Head (Honey brown fur, round snout, nose, mouth socket)
    im_head = Image.new("RGBA", (360, 340), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_head)
    # Bear ears
    d.ellipse([40, 20, 115, 95], fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=4)
    d.ellipse([58, 38, 98, 78], fill=(115, 70, 35, 255))
    d.ellipse([245, 20, 320, 95], fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=4)
    d.ellipse([262, 38, 302, 78], fill=(115, 70, 35, 255))
    # Head Base
    d.ellipse([45, 45, 315, 305], fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=4)
    # Light cream muzzle/snout
    d.ellipse([110, 155, 250, 265], fill=(245, 220, 180, 255), outline=(60, 40, 30, 255), width=3)
    # Cute dark triangular nose
    d.polygon([(160, 175), (200, 175), (180, 198)], fill=(40, 30, 30, 255))
    d.ellipse([172, 178, 184, 186], fill=(255, 255, 255, 180))  # highlight
    im_head.save(os.path.join(CHARACTERS_DIR, "golu_head.png"))

    # 2. Torso (Chubby honey brown body with light cream belly patch)
    im_torso = Image.new("RGBA", (320, 340), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_torso)
    d.ellipse([40, 35, 280, 305], fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=4)
    # Cream belly oval
    d.ellipse([75, 90, 245, 285], fill=(245, 220, 180, 255), outline=(70, 45, 35, 255), width=2)
    im_torso.save(os.path.join(CHARACTERS_DIR, "golu_torso.png"))

    # 3. Knitted Yellow Scarf
    im_scarf = Image.new("RGBA", (280, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_scarf)
    # Main wrap around neck
    d.rounded_rectangle([30, 20, 250, 75], radius=18, fill=(255, 214, 10, 255), outline=(60, 45, 20, 255), width=3)
    # Hanging scarf tail with fringe
    d.polygon([(150, 65), (205, 65), (195, 145), (140, 145)], fill=(255, 214, 10, 255), outline=(60, 45, 20, 255), width=3)
    # Fringe lines
    for fx in range(145, 195, 8):
        d.line([(fx, 145), (fx - 2, 158)], fill=(200, 160, 10, 255), width=2)
    im_scarf.save(os.path.join(CHARACTERS_DIR, "golu_scarf.png"))

    # 4. Upper Arm & Lower Arm (Paws)
    im_uarm = Image.new("RGBA", (85, 125), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_uarm)
    d.rounded_rectangle([15, 10, 70, 115], radius=22, fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=3)
    im_uarm.save(os.path.join(CHARACTERS_DIR, "golu_arm_upper.png"))

    im_larm = Image.new("RGBA", (90, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_larm)
    d.rounded_rectangle([15, 10, 75, 85], radius=20, fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=3)
    # Chubby Bear Paw
    d.ellipse([10, 60, 80, 120], fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=3)
    d.ellipse([25, 75, 65, 110], fill=(245, 220, 180, 220))  # paw pad
    im_larm.save(os.path.join(CHARACTERS_DIR, "golu_arm_lower.png"))

    # 5. Upper Leg & Lower Leg (Bear Foot)
    im_uleg = Image.new("RGBA", (90, 125), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_uleg)
    d.rounded_rectangle([15, 10, 75, 115], radius=22, fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=3)
    im_uleg.save(os.path.join(CHARACTERS_DIR, "golu_leg_upper.png"))

    im_lleg = Image.new("RGBA", (105, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_lleg)
    d.rounded_rectangle([20, 10, 80, 80], radius=20, fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=3)
    # Foot
    d.ellipse([10, 60, 95, 122], fill=(155, 95, 50, 255), outline=(50, 35, 30, 255), width=3)
    d.ellipse([28, 75, 78, 112], fill=(245, 220, 180, 220))
    im_lleg.save(os.path.join(CHARACTERS_DIR, "golu_leg_lower.png"))

    # 6. Eyes (6 states)
    for state in ["open", "blink", "happy", "sad", "surprised", "look_down"]:
        im_eye = Image.new("RGBA", (65, 65), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_eye)
        if state == "open":
            d.ellipse([10, 10, 54, 54], fill=(255, 255, 255, 255), outline=(40, 30, 30, 255), width=3)
            d.ellipse([22, 18, 48, 48], fill=(65, 45, 35, 255))
            d.ellipse([26, 22, 44, 44], fill=(15, 15, 15, 255))
            d.ellipse([30, 24, 38, 32], fill=(255, 255, 255, 255))
        elif state == "blink":
            d.arc([10, 20, 54, 45], start=0, end=180, fill=(40, 30, 30, 255), width=4)
        elif state == "happy":
            d.arc([10, 14, 54, 44], start=180, end=360, fill=(40, 30, 30, 255), width=4)
        elif state == "sad":
            d.ellipse([10, 14, 54, 54], fill=(255, 255, 255, 255), outline=(40, 30, 30, 255), width=3)
            d.ellipse([20, 24, 46, 50], fill=(65, 45, 35, 255))
            d.ellipse([24, 28, 42, 46], fill=(15, 15, 15, 255))
            # small tear drop
            d.ellipse([36, 44, 46, 56], fill=(135, 206, 250, 220))
        elif state == "surprised":
            d.ellipse([6, 6, 58, 58], fill=(255, 255, 255, 255), outline=(40, 30, 30, 255), width=3)
            d.ellipse([20, 16, 48, 48], fill=(65, 45, 35, 255))
            d.ellipse([24, 20, 44, 44], fill=(15, 15, 15, 255))
            d.ellipse([30, 22, 40, 32], fill=(255, 255, 255, 255))
        elif state == "look_down":
            d.ellipse([10, 10, 54, 54], fill=(255, 255, 255, 255), outline=(40, 30, 30, 255), width=3)
            d.ellipse([20, 26, 48, 52], fill=(65, 45, 35, 255))
            d.ellipse([24, 30, 44, 50], fill=(15, 15, 15, 255))
        im_eye.save(os.path.join(CHARACTERS_DIR, f"golu_eye_{state}.png"))

    # 7. Eyebrows
    for b_state in ["neutral", "sad", "happy", "surprised"]:
        im_b = Image.new("RGBA", (60, 35), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_b)
        if b_state == "neutral":
            d.line([(10, 18), (50, 18)], fill=(60, 40, 30, 255), width=4)
        elif b_state == "sad":
            d.line([(10, 12), (50, 24)], fill=(60, 40, 30, 255), width=4)
        elif b_state == "happy":
            d.arc([10, 6, 50, 30], start=180, end=360, fill=(60, 40, 30, 255), width=4)
        elif b_state == "surprised":
            d.arc([10, 2, 50, 22], start=180, end=360, fill=(60, 40, 30, 255), width=4)
        im_b.save(os.path.join(CHARACTERS_DIR, f"golu_brow_{b_state}.png"))

    # 8. Mouth Visemes
    visemes = ["smile", "sad", "open_ah", "wide_ee", "round_oh", "munch_crunch"]
    for v in visemes:
        im_m = Image.new("RGBA", (75, 55), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_m)
        if v == "smile":
            d.arc([15, 12, 60, 36], start=0, end=180, fill=(50, 35, 30, 255), width=4)
        elif v == "sad":
            d.arc([15, 24, 60, 48], start=180, end=360, fill=(50, 35, 30, 255), width=4)
        elif v == "open_ah":
            d.chord([15, 10, 60, 46], start=0, end=180, fill=(180, 45, 55, 255), outline=(50, 35, 30, 255), width=3)
            d.ellipse([24, 28, 51, 44], fill=(255, 130, 140, 255))
        elif v == "wide_ee":
            d.rounded_rectangle([12, 16, 62, 36], radius=8, fill=(180, 45, 55, 255), outline=(50, 35, 30, 255), width=3)
            d.rectangle([18, 18, 56, 24], fill=(255, 255, 255, 255))
        elif v == "round_oh":
            d.ellipse([22, 10, 53, 44], fill=(180, 45, 55, 255), outline=(50, 35, 30, 255), width=3)
        elif v == "munch_crunch":
            d.polygon([(18, 25), (30, 15), (45, 28), (56, 18), (48, 34), (25, 32)], fill=(180, 45, 55, 255), outline=(50, 35, 30, 255), width=3)
        im_m.save(os.path.join(CHARACTERS_DIR, f"golu_mouth_{v}.png"))


# =====================================================================
# 3. PROPS & ENVIRONMENTAL ASSETS
# =====================================================================

def generate_props_and_effects():
    """Generates whole apple, split halves, bitten halves, butterfly, dandelions, sparkles, sunbeams."""
    # 1. Whole Apple
    im_apple = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_apple)
    # Apple Body (deep ruby red with bright gloss highlight)
    d.ellipse([25, 35, 155, 165], fill=(230, 45, 55, 255), outline=(80, 20, 25, 255), width=3)
    d.ellipse([45, 50, 85, 95], fill=(255, 140, 150, 255))  # glossy sheen
    d.ellipse([55, 60, 75, 80], fill=(255, 255, 255, 240))  # specular core
    # Brown Stem
    d.line([(90, 45), (105, 15)], fill=(100, 60, 30, 255), width=6)
    # Green Leaf
    d.ellipse([100, 10, 145, 35], fill=(70, 180, 80, 255), outline=(30, 80, 40, 255), width=2)
    im_apple.save(os.path.join(PROPS_DIR, "apple_whole.png"))

    # 2. Apple Halves (Chintu & Golu - showing cream flesh & dark seeds)
    for name, facing in [("apple_half_chintu", 1), ("apple_half_golu", -1)]:
        im_half = Image.new("RGBA", (140, 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_half)
        # Red outer skin curve
        d.chord([15, 20, 125, 150], start=270, end=90, fill=(230, 45, 55, 255), outline=(80, 20, 25, 255), width=3)
        # Cream inner flesh
        d.chord([25, 24, 115, 146], start=270, end=90, fill=(255, 244, 210, 255))
        # Core & dark apple seeds
        d.ellipse([55, 70, 80, 100], fill=(245, 220, 175, 255))
        d.ellipse([62, 76, 72, 88], fill=(60, 30, 20, 255))
        d.ellipse([64, 90, 74, 100], fill=(60, 30, 20, 255))
        # Stem piece on top
        d.line([(70, 22), (75, 8)], fill=(100, 60, 30, 255), width=4)
        if facing < 0:
            im_half = im_half.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        im_half.save(os.path.join(PROPS_DIR, f"{name}.png"))

    # 3. Bitten Apple Halves (with scallop bite marks)
    for name, facing in [("apple_bitten_chintu", 1), ("apple_bitten_golu", -1)]:
        im_bitten = Image.new("RGBA", (140, 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_bitten)
        d.chord([15, 20, 125, 150], start=270, end=90, fill=(230, 45, 55, 255), outline=(80, 20, 25, 255), width=3)
        d.chord([25, 24, 115, 146], start=270, end=90, fill=(255, 244, 210, 255))
        d.ellipse([55, 75, 80, 105], fill=(245, 220, 175, 255))
        d.ellipse([64, 82, 74, 96], fill=(60, 30, 20, 255))
        # Cutout bite marks on outer skin
        d.ellipse([80, 30, 120, 70], fill=(0, 0, 0, 0))  # bite 1
        d.ellipse([95, 55, 130, 95], fill=(0, 0, 0, 0))   # bite 2
        if facing < 0:
            im_bitten = im_bitten.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        im_bitten.save(os.path.join(PROPS_DIR, f"{name}.png"))

    # 4. Animated Butterfly (2 frames for fluttering wing cycle)
    for frame in [1, 2]:
        im_bf = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        d = ImageDraw.Draw(im_bf)
        w_span = 38 if frame == 1 else 16
        # Top wings
        d.ellipse([50 - w_span, 15, 50, 55], fill=(0, 210, 255, 235), outline=(0, 90, 150, 255), width=2)
        d.ellipse([50, 15, 50 + w_span, 55], fill=(0, 210, 255, 235), outline=(0, 90, 150, 255), width=2)
        # Bottom wings
        d.ellipse([50 - int(w_span * 0.75), 45, 50, 75], fill=(255, 225, 50, 235), outline=(160, 130, 20, 255), width=2)
        d.ellipse([50, 45, 50 + int(w_span * 0.75), 75], fill=(255, 225, 50, 235), outline=(160, 130, 20, 255), width=2)
        # Body
        d.rounded_rectangle([47, 28, 53, 68], radius=3, fill=(50, 40, 40, 255))
        # Antennae
        d.line([(48, 28), (40, 15)], fill=(50, 40, 40, 255), width=2)
        d.line([(52, 28), (60, 15)], fill=(50, 40, 40, 255), width=2)
        im_bf.save(os.path.join(PROPS_DIR, f"butterfly_frame{frame}.png"))

    # 5. Dandelion Seed Puff Particle
    im_dp = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_dp)
    # Seed
    d.ellipse([23, 32, 27, 44], fill=(120, 95, 65, 240))
    d.line([(25, 32), (25, 14)], fill=(230, 230, 230, 220), width=2)
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        ex = 25 + int(math.cos(rad) * 12)
        ey = 14 + int(math.sin(rad) * 12)
        d.line([(25, 14), (ex, ey)], fill=(255, 255, 255, 190), width=1)
    im_dp.save(os.path.join(PROPS_DIR, "dandelion_puff.png"))

    # 6. Green Leaf Particle
    im_leaf = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_leaf)
    d.ellipse([10, 15, 50, 45], fill=(85, 185, 75, 240), outline=(40, 110, 35, 255), width=2)
    d.line([(10, 30), (50, 30)], fill=(50, 130, 40, 255), width=2)
    im_leaf.save(os.path.join(PROPS_DIR, "leaf_particle.png"))

    # 7. Golden Sparkle Starburst
    im_sp = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_sp)
    cx, cy = 90, 90
    for p in range(8):
        ang = p * (2 * math.pi / 8)
        rad_outer = 85 if p % 2 == 0 else 42
        ex = cx + int(math.cos(ang) * rad_outer)
        ey = cy + int(math.sin(ang) * rad_outer)
        d.line([(cx, cy), (ex, ey)], fill=(255, 215, 0, 240), width=5 if p % 2 == 0 else 3)
    d.ellipse([70, 70, 110, 110], fill=(255, 250, 190, 255))
    d.ellipse([78, 78, 102, 102], fill=(255, 255, 255, 255))
    im_sp.save(os.path.join(PROPS_DIR, "sparkle_gold.png"))

    # 8. Musical Note
    im_mn = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_mn)
    d.ellipse([18, 52, 42, 74], fill=(235, 65, 140, 255))
    d.ellipse([54, 40, 78, 62], fill=(235, 65, 140, 255))
    d.line([(39, 62), (39, 18)], fill=(235, 65, 140, 255), width=5)
    d.line([(75, 50), (75, 12)], fill=(235, 65, 140, 255), width=5)
    d.polygon([(39, 18), (75, 12), (75, 24), (39, 30)], fill=(235, 65, 140, 255))
    im_mn.save(os.path.join(PROPS_DIR, "music_note.png"))

    # 9. Sunbeam
    im_sb = Image.new("RGBA", (600, 800), (0, 0, 0, 0))
    d = ImageDraw.Draw(im_sb)
    d.polygon([(100, 0), (250, 0), (550, 800), (350, 800)], fill=(255, 250, 200, 45))
    im_sb.save(os.path.join(PROPS_DIR, "sunbeam.png"))


def main():
    print("🎨 Generating Cartoon Version 2 High-Res Assets...", flush=True)
    ensure_dirs()

    print("  [1/3] Generating 18 Parallax Background Layers (6 Scenes)...", flush=True)
    generate_scene1_forest_meadow()
    generate_scene2_the_great_tree()
    generate_scene3_woodland_path()
    generate_scene4_sunlit_clearing()
    generate_scene5_picnic_glade()
    generate_scene6_sunset_outlook()

    print("  [2/3] Generating Articulated Character Parts (Chintu & Golu)...", flush=True)
    generate_chintu_bunny_parts()
    generate_golu_bear_parts()

    print("  [3/3] Generating Props & Environmental Particle Assets...", flush=True)
    generate_props_and_effects()

    print("✅ All Version 2 Assets generated successfully!", flush=True)


if __name__ == "__main__":
    main()
