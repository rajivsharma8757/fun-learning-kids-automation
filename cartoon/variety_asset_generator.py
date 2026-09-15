"""
variety_asset_generator.py
--------------------------
Generates studio-grade visual assets for the Cartoon Variety System:
1. Diverse Background Environments for V1:
   - sunny_farm.png
   - treehouse_canopy.png
   - pond_park.png
2. Multi-Plane Parallax Environments for V4 (1920x1080):
   - science_lab (Far, Mid, FG)
   - starry_space (Far, Mid, FG)
   - magic_library (Far, Mid, FG)
   - blooming_garden (Far, Mid, FG)
3. Diverse Character Assets for V4:
   - Robo-Bantu (friendly tin-robot)
   - Aarav (explorer boy)
   - Tara (star fairy)
4. Diverse Character Assets for V1:
   - Koko (squirrel)
   - Bholu (puppy)
   - Leo (friendly lion cub)
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_DIR

BG_V1_DIR = os.path.join(CARTOON_DIR, "assets", "backgrounds")
CHAR_V1_DIR = os.path.join(CARTOON_DIR, "assets", "characters")
PROPS_V1_DIR = os.path.join(CARTOON_DIR, "assets", "props")

BG_V4_DIR = os.path.join(CARTOON_DIR, "assets_v3", "backgrounds")
CHAR_V4_DIR = os.path.join(CARTOON_DIR, "assets_v3", "characters")
PROPS_V4_DIR = os.path.join(CARTOON_DIR, "assets_v3", "props")

for d in [BG_V1_DIR, CHAR_V1_DIR, PROPS_V1_DIR, BG_V4_DIR, CHAR_V4_DIR, PROPS_V4_DIR]:
    os.makedirs(d, exist_ok=True)


def draw_circle(draw, center, radius, fill, outline=None, width=1):
    x, y = center
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill, outline=outline, width=width)


# =========================================================================
# 1. V1 BACKGROUNDS (1920x1080)
# =========================================================================
def generate_v1_farm():
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Blue Sunny Sky
    for y in range(h):
        r = int(135 + (y / h) * 45)
        g = int(210 + (y / h) * 35)
        b = 255
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Sun & Clouds
    draw_circle(d, (1600, 160), 65, fill=(255, 235, 70, 255), outline=(255, 200, 40, 255), width=4)
    for cx, cy, sz in [(300, 140, 75), (800, 120, 65), (1250, 150, 80)]:
        draw_circle(d, (cx - 30, cy), sz * 0.7, fill=(255, 255, 255, 240))
        draw_circle(d, (cx + 30, cy), sz * 0.75, fill=(255, 255, 255, 240))
        draw_circle(d, (cx, cy - 20), sz * 0.85, fill=(255, 255, 255, 255))

    # Distant Red Barn on Hill
    d.pieslice([850, 380, 2100, 1200], start=180, end=360, fill=(120, 185, 120, 255))
    barn_x, barn_y = 1250, 480
    d.rectangle([barn_x, barn_y, barn_x + 220, barn_y + 150], fill=(210, 50, 45, 255), outline=(150, 30, 30, 255), width=3)
    d.polygon([(barn_x - 20, barn_y), (barn_x + 110, barn_y - 80), (barn_x + 240, barn_y)], fill=(240, 240, 245, 255), outline=(120, 120, 130, 255), width=3)
    d.rectangle([barn_x + 80, barn_y + 60, barn_x + 140, barn_y + 150], fill=(255, 255, 255, 255))
    d.line([(barn_x + 80, barn_y + 60), (barn_x + 140, barn_y + 150)], fill=(210, 50, 45, 255), width=3)

    # Main Pasture Hill
    d.pieslice([-150, 450, 1400, 1300], start=180, end=360, fill=(95, 175, 95, 255))
    d.rectangle([0, 720, w, h], fill=(70, 155, 70, 255))

    # White Picket Fence across midground
    for fx in range(60, w - 60, 65):
        d.polygon([(fx, 650), (fx + 16, 630), (fx + 32, 650), (fx + 32, 730), (fx, 730)], fill=(250, 250, 250, 255), outline=(200, 200, 200, 255), width=2)
    d.rectangle([50, 660, w - 50, 675], fill=(245, 245, 245, 255), outline=(190, 190, 190, 255), width=2)
    d.rectangle([50, 695, w - 50, 710], fill=(245, 245, 245, 255), outline=(190, 190, 190, 255), width=2)

    # Sunflowers in foreground corner
    for sx in [100, 170, 240]:
        d.line([(sx, 850), (sx, 740)], fill=(60, 130, 50, 255), width=8)
        for ang in range(0, 360, 30):
            rad = math.radians(ang)
            px = sx + math.cos(rad) * 35
            py = 740 + math.sin(rad) * 35
            draw_circle(d, (px, py), 14, fill=(255, 215, 0, 255))
        draw_circle(d, (sx, 740), 22, fill=(100, 60, 20, 255))

    out_p = os.path.join(BG_V1_DIR, "sunny_farm.png")
    im.save(out_p, "PNG")
    print("Generated:", out_p)


def generate_v1_pond():
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Sky
    for y in range(h):
        d.line([(0, y), (w, y)], fill=(130 + int(y/h * 40), 215 + int(y/h * 30), 255, 255))

    # Hills
    d.pieslice([-100, 420, 1100, 1200], start=180, end=360, fill=(110, 190, 130, 255))
    d.pieslice([800, 440, 2000, 1200], start=180, end=360, fill=(125, 200, 140, 255))

    # Park lawn
    d.rectangle([0, 680, w, h], fill=(85, 175, 95, 255))

    # Winding Blue Duck Pond
    d.ellipse([250, 720, 1680, 1040], fill=(70, 170, 230, 255), outline=(180, 220, 250, 255), width=6)
    d.ellipse([320, 750, 1610, 1000], fill=(55, 155, 220, 255))

    # Lily pads & pink lotus
    for lx, ly in [(450, 820), (750, 880), (1200, 810), (1450, 860)]:
        d.ellipse([lx - 45, ly - 22, lx + 45, ly + 22], fill=(50, 160, 80, 255), outline=(35, 120, 60, 255), width=2)
        # Flower
        draw_circle(d, (lx - 10, ly - 10), 12, fill=(255, 150, 180, 255))
        draw_circle(d, (lx + 8, ly - 12), 11, fill=(255, 180, 200, 255))
        draw_circle(d, (lx, ly - 8), 7, fill=(255, 240, 100, 255))

    # Wooden Arched Footbridge in background
    d.pieslice([1000, 640, 1450, 820], start=180, end=360, fill=(160, 105, 60, 255), outline=(120, 75, 40, 255), width=4)
    d.pieslice([1050, 670, 1400, 830], start=180, end=360, fill=(85, 175, 95, 255))

    out_p = os.path.join(BG_V1_DIR, "pond_park.png")
    im.save(out_p, "PNG")
    print("Generated:", out_p)


def generate_v1_treehouse():
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Sunny Sky with morning gradient
    for y in range(h):
        d.line([(0, y), (w, y)], fill=(145 + int(y/h*50), 220 + int(y/h*25), 255, 255))

    # Giant Oak Trunk on Left
    d.polygon([(180, 0), (320, 0), (450, h), (120, h)], fill=(120, 75, 40, 255), outline=(90, 50, 25, 255), width=5)
    # Huge Branches stretching across
    d.polygon([(300, 480), (1200, 380), (1220, 450), (310, 560)], fill=(120, 75, 40, 255))

    # Wooden Treehouse Platform on Branch
    d.rectangle([650, 340, 1150, 400], fill=(185, 125, 75, 255), outline=(130, 85, 45, 255), width=4)
    # Treehouse Cabin
    d.rectangle([720, 180, 1080, 340], fill=(210, 150, 95, 255), outline=(140, 95, 55, 255), width=4)
    # Window with yellow light
    d.rectangle([850, 220, 950, 300], fill=(255, 240, 150, 255), outline=(130, 85, 45, 255), width=3)
    d.line([(900, 220), (900, 300)], fill=(130, 85, 45, 255), width=3)
    d.line([(850, 260), (950, 260)], fill=(130, 85, 45, 255), width=3)
    # Green Leafy Roof
    d.polygon([(680, 190), (900, 90), (1120, 190)], fill=(50, 140, 60, 255), outline=(35, 100, 40, 255), width=4)

    # Canopy Leaves clustering top and sides
    for cx, cy, sz in [(200, 120, 160), (500, 150, 140), (1150, 160, 150), (1400, 280, 160), (1700, 220, 180)]:
        draw_circle(d, (cx, cy), sz, fill=(55, 155, 65, 240))
        draw_circle(d, (cx - 15, cy - 15), sz * 0.85, fill=(75, 180, 85, 255))

    # Ground far below
    d.rectangle([0, 820, w, h], fill=(65, 150, 75, 255))

    out_p = os.path.join(BG_V1_DIR, "treehouse_canopy.png")
    im.save(out_p, "PNG")
    print("Generated:", out_p)


# =========================================================================
# 2. V4 MULTI-PLANE BACKGROUNDS (1920x1080)
# =========================================================================
def generate_v4_science_lab():
    w, h = 1920, 1080
    # Far: Lab Wall & Chalkboard
    far = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_far = ImageDraw.Draw(far)
    for y in range(h):
        d_far.line([(0, y), (w, y)], fill=(225 - int(y/h*30), 235 - int(y/h*25), 245, 255))
    # Chalkboard in center
    d_far.rectangle([550, 160, 1370, 560], fill=(40, 65, 55, 255), outline=(160, 120, 75, 255), width=12)
    d_far.text((620, 220), "E = mc²  ★  H₂O", fill=(240, 240, 240, 240), font=None)
    # Beaker Shelves
    d_far.rectangle([140, 250, 480, 275], fill=(170, 130, 85, 255))
    d_far.rectangle([1440, 250, 1780, 275], fill=(170, 130, 85, 255))
    far.save(os.path.join(BG_V4_DIR, "bg_lab_far.png"))

    # Mid: High-Tech Lab Work Desk & Floor
    mid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_mid = ImageDraw.Draw(mid)
    # Tiled Lab Floor
    d_mid.rectangle([0, 620, w, h], fill=(215, 225, 235, 255))
    for fx in range(0, w, 120):
        d_mid.line([(fx, 620), (fx, h)], fill=(195, 205, 215, 255), width=2)
    # Lab Desk
    d_mid.rectangle([200, 560, 1720, 680], fill=(240, 245, 250, 255), outline=(180, 195, 210, 255), width=4)
    # Colorful Beakers & Flasks on Desk
    colors = [(255, 80, 80), (80, 180, 255), (255, 220, 50), (120, 240, 100)]
    for idx, col in enumerate(colors):
        bx = 1200 + idx * 85
        d_mid.polygon([(bx + 15, 480), (bx + 25, 480), (bx + 50, 560), (bx - 10, 560)], fill=(col[0], col[1], col[2], 210), outline=(255, 255, 255, 255), width=2)
    mid.save(os.path.join(BG_V4_DIR, "bg_lab_mid.png"))

    # FG: Soft blurred magnifying desk lamp
    fg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_fg = ImageDraw.Draw(fg)
    draw_circle(d_fg, (120, 880), 90, fill=(70, 130, 180, 180), outline=(255, 255, 255, 220), width=8)
    d_fg.line([(120, 970), (120, 1080)], fill=(90, 100, 110, 240), width=18)
    fg_blur = fg.filter(ImageFilter.GaussianBlur(radius=5))
    fg_blur.save(os.path.join(BG_V4_DIR, "bg_lab_fg.png"))
    print("Generated: Science Lab (Far, Mid, FG)")


def generate_v4_space():
    w, h = 1920, 1080
    # Far: Cosmic Indigo Gradient & Stars
    far = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_far = ImageDraw.Draw(far)
    for y in range(h):
        r = int(12 + (y / h) * 35)
        g = int(15 + (y / h) * 25)
        b = int(45 + (y / h) * 60)
        d_far.line([(0, y), (w, y)], fill=(r, g, b, 255))
    # Nebula glow
    d_far.ellipse([600, 120, 1500, 650], fill=(120, 50, 180, 75))
    # Twinkling Stars
    import random
    random.seed(101)
    for _ in range(160):
        sx, sy = random.randint(30, w - 30), random.randint(30, 700)
        s_rad = random.randint(2, 5)
        draw_circle(d_far, (sx, sy), s_rad, fill=(255, 255, 255, 230))
    far.save(os.path.join(BG_V4_DIR, "bg_space_far.png"))

    # Mid: Golden Crescent Moon, Saturn Planet, & Observation Deck
    mid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_mid = ImageDraw.Draw(mid)
    # Golden Crescent Moon on left
    draw_circle(d_mid, (360, 240), 90, fill=(255, 235, 120, 255))
    draw_circle(d_mid, (400, 225), 85, fill=(18, 22, 58, 255))
    # Ringed Cartoon Planet on right
    px, py = 1500, 260
    draw_circle(d_mid, (px, py), 75, fill=(245, 140, 90, 255))
    d_mid.ellipse([px - 140, py - 25, px + 140, py + 25], outline=(255, 215, 140, 230), width=10)
    # Starlight Platform / Cosmic Deck Floor
    d_mid.rectangle([0, 700, w, h], fill=(30, 45, 80, 255), outline=(75, 130, 220, 255), width=4)
    mid.save(os.path.join(BG_V4_DIR, "bg_space_mid.png"))

    # FG: Twinkling stardust frame
    fg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_fg = ImageDraw.Draw(fg)
    draw_circle(d_fg, (1800, 920), 40, fill=(255, 240, 160, 200))
    draw_circle(d_fg, (120, 950), 30, fill=(255, 240, 160, 180))
    fg_blur = fg.filter(ImageFilter.GaussianBlur(radius=4))
    fg_blur.save(os.path.join(BG_V4_DIR, "bg_space_fg.png"))
    print("Generated: Starry Space (Far, Mid, FG)")


# =========================================================================
# 3. V4 CHARACTERS (Studio Cutouts)
# =========================================================================
def generate_v4_robo_bantu():
    """Generates Robo-Bantu: friendly tin-robot cutout with LED smile & antennae."""
    w, h = 480, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Antenna & Yellow Bulb
    d.line([(240, 110), (240, 50)], fill=(120, 140, 160, 255), width=10)
    draw_circle(d, (240, 45), 24, fill=(255, 230, 40, 255), outline=(220, 180, 20, 255), width=3)

    # Robot Head (Rounded metallic cyan box)
    head_box = [110, 100, 370, 300]
    d.rounded_rectangle(head_box, radius=35, fill=(90, 190, 215, 255), outline=(50, 130, 160, 255), width=6)

    # Visor Screen (Deep blue glass)
    screen_box = [140, 135, 340, 265]
    d.rounded_rectangle(screen_box, radius=22, fill=(25, 45, 75, 255), outline=(60, 160, 190, 255), width=4)

    # Ear dials
    d.rounded_rectangle([80, 170, 115, 230], radius=10, fill=(255, 140, 60, 255))
    d.rounded_rectangle([365, 170, 400, 230], radius=10, fill=(255, 140, 60, 255))

    # Neck
    d.rectangle([210, 300, 270, 335], fill=(130, 150, 170, 255), outline=(90, 110, 130, 255), width=3)

    # Robot Body (Sturdy rounded box with chest gauges)
    body_box = [120, 330, 360, 530]
    d.rounded_rectangle(body_box, radius=30, fill=(80, 180, 205, 255), outline=(50, 130, 160, 255), width=6)

    # Chest Screen / Heart meter
    d.rounded_rectangle([170, 365, 310, 450], radius=16, fill=(245, 250, 255, 255), outline=(60, 150, 180, 255), width=3)
    # Cute battery gauge bars (green)
    d.rounded_rectangle([190, 385, 290, 405], radius=6, fill=(76, 175, 80, 255))
    d.rounded_rectangle([190, 415, 290, 435], radius=6, fill=(76, 175, 80, 255))

    # Shoulders
    draw_circle(d, (100, 365), 26, fill=(255, 160, 60, 255))
    draw_circle(d, (380, 365), 26, fill=(255, 160, 60, 255))

    out_p = os.path.join(CHAR_V4_DIR, "bantu_base.png")
    im.save(out_p, "PNG")
    print("Generated:", out_p)


def generate_v4_aarav():
    """Generates Aarav the Explorer boy: cute stylized cartoon character."""
    w, h = 480, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Head (Warm skin tone)
    head_box = [140, 120, 340, 310]
    d.rounded_rectangle(head_box, radius=60, fill=(255, 215, 175, 255), outline=(220, 170, 130, 255), width=4)

    # Explorer Cap (Vibrant orange with blue brim)
    d.pieslice([110, 60, 370, 210], start=180, end=360, fill=(255, 130, 40, 255), outline=(200, 90, 20, 255), width=4)
    d.rounded_rectangle([120, 125, 380, 160], radius=14, fill=(40, 130, 220, 255), outline=(25, 90, 170, 255), width=3)

    # Cute Ears with rosy cheeks
    draw_circle(d, (135, 225), 20, fill=(255, 210, 170, 255))
    draw_circle(d, (345, 225), 20, fill=(255, 210, 170, 255))
    draw_circle(d, (175, 255), 18, fill=(255, 160, 160, 140))
    draw_circle(d, (305, 255), 18, fill=(255, 160, 160, 140))

    # Body (Yellow explorer t-shirt + blue dungarees)
    d.rounded_rectangle([140, 310, 340, 520], radius=35, fill=(255, 210, 50, 255), outline=(210, 165, 30, 255), width=4)
    # Dungaree Straps
    d.rectangle([180, 330, 215, 520], fill=(50, 120, 210, 255))
    d.rectangle([265, 330, 300, 520], fill=(50, 120, 210, 255))
    # Big brass buttons
    draw_circle(d, (197, 410), 10, fill=(255, 225, 70, 255))
    draw_circle(d, (282, 410), 10, fill=(255, 225, 70, 255))

    out_p = os.path.join(CHAR_V4_DIR, "aarav_base.png")
    im.save(out_p, "PNG")
    print("Generated:", out_p)


if __name__ == "__main__":
    generate_v1_farm()
    generate_v1_pond()
    generate_v1_treehouse()
    generate_v4_science_lab()
    generate_v4_space()
    generate_v4_robo_bantu()
    generate_v4_aarav()
    print("ALL VARIETY ASSETS GENERATED SUCCESSFULLY!")
