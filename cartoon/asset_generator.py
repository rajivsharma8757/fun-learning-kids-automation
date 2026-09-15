import os
import sys
import math
import random
sys.path.insert(0, r"C:\kids_automation")

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from PIL import Image, ImageDraw, ImageFilter
from cartoon.config import ASSETS_DIR, CHARACTERS_DIR, BACKGROUNDS_DIR, PROPS_DIR

def draw_circle(draw, center, radius, fill, outline=None, width=1):
    x, y = center
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill, outline=outline, width=width)

def generate_background():
    w, h = 1920, 1080
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # 1. Sky Gradient
    for y in range(h):
        r = int(125 + (y / h) * 40)
        g = int(205 + (y / h) * 30)
        b = 255
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Sun with soft radial glow
    sun_x, sun_y = 1550, 180
    for r in range(140, 70, -6):
        alpha = int(12 + (140 - r) * 2.5)
        draw_circle(draw, (sun_x, sun_y), r, fill=(255, 245, 180, alpha))
    draw_circle(draw, (sun_x, sun_y), 70, fill=(255, 230, 80, 255), outline=(255, 210, 50, 255), width=4)

    # 2. Clouds
    clouds = [(220, 130, 70), (550, 190, 85), (950, 120, 65), (1320, 160, 80), (1750, 130, 75)]
    for cx, cy, sz in clouds:
        for ox, oy, r in [(-sz*0.6, sz*0.2, sz*0.7), (0, -sz*0.3, sz*0.9), (sz*0.6, sz*0.2, sz*0.75), (0, sz*0.3, sz*0.8)]:
            draw_circle(draw, (cx + ox, cy + oy), r, fill=(255, 255, 255, 245))
        draw_circle(draw, (cx, cy), sz * 0.85, fill=(255, 255, 255, 255))

    # 3. Distant Mountains (Soft Parallax)
    draw.pieslice([-200, 420, 900, 1100], start=180, end=360, fill=(140, 195, 175, 255))
    draw.pieslice([600, 400, 1700, 1100], start=180, end=360, fill=(130, 185, 165, 255))
    draw.pieslice([1400, 440, 2300, 1100], start=180, end=360, fill=(145, 200, 180, 255))

    # 4. Midground Rolling Hills
    draw.pieslice([-100, 500, 1100, 1250], start=180, end=360, fill=(102, 187, 106, 255))
    draw.pieslice([800, 480, 2100, 1250], start=180, end=360, fill=(129, 199, 132, 255))

    # 5. Foreground Main Ground
    draw.pieslice([100, 560, 1800, 1350], start=180, end=360, fill=(76, 175, 80, 255))
    draw.rectangle([0, 750, w, h], fill=(67, 160, 71, 255))

    # Wildflowers
    random.seed(42)
    for _ in range(120):
        gx = random.randint(40, w - 40)
        gy = random.randint(700, h - 20)
        col = random.choice([(255, 235, 59), (244, 67, 54), (255, 255, 255), (255, 152, 0)])
        draw_circle(draw, (gx, gy), random.randint(4, 7), fill=col)
        draw_circle(draw, (gx, gy), 2, fill=(255, 215, 0))

    bg_path = os.path.join(BACKGROUNDS_DIR, 'forest_meadow.png')
    im.save(bg_path, 'PNG')
    print('Generated background:', bg_path)

def generate_oak_tree():
    w, h = 600, 700
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Trunk & Roots
    trunk_color = (139, 90, 43, 255)
    bark_dark = (101, 67, 33, 255)
    draw.polygon([(260, 300), (340, 300), (380, 680), (440, 700), (160, 700), (220, 680)], fill=trunk_color)
    # Bark texture lines
    for bx in [270, 300, 330]:
        draw.line([(bx, 340), (bx - 10, 660)], fill=bark_dark, width=3)

    # Branches
    draw.line([(270, 380), (160, 280)], fill=trunk_color, width=28)
    draw.line([(330, 360), (450, 260)], fill=trunk_color, width=24)

    # Lush Leaf Canopy Clusters
    leaf_dark = (46, 125, 50, 255)
    leaf_mid = (76, 175, 80, 255)
    leaf_light = (129, 199, 132, 255)

    clusters = [
        (300, 180, 140), (180, 240, 120), (420, 220, 130),
        (220, 120, 110), (380, 110, 115), (300, 80, 100)
    ]
    for cx, cy, rad in clusters:
        draw_circle(draw, (cx, cy), rad, fill=leaf_dark)
        draw_circle(draw, (cx - 10, cy - 10), rad * 0.88, fill=leaf_mid)
        draw_circle(draw, (cx - 25, cy - 25), rad * 0.55, fill=leaf_light)

    path = os.path.join(BACKGROUNDS_DIR, 'oak_tree.png')
    im.save(path, 'PNG')
    print('Generated oak tree:', path)

def generate_props():
    # 1. Whole Giant Red Apple
    w, h = 260, 260
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Stem
    draw.line([(130, 80), (145, 30)], fill=(110, 65, 25, 255), width=8)
    # Leaf
    draw.pieslice([140, 20, 210, 65], start=210, end=360, fill=(76, 175, 80, 255), outline=(56, 142, 60, 255), width=2)

    # Red Apple lobes
    apple_red = (229, 57, 53, 255)
    apple_dark = (198, 40, 40, 255)
    draw_circle(draw, (105, 150), 75, fill=apple_dark)
    draw_circle(draw, (155, 150), 75, fill=apple_dark)
    draw_circle(draw, (105, 148), 70, fill=apple_red)
    draw_circle(draw, (155, 148), 70, fill=apple_red)
    # Highlight gleam
    draw_circle(draw, (85, 115), 18, fill=(255, 255, 255, 200))
    draw_circle(draw, (75, 135), 8, fill=(255, 255, 255, 160))

    im.save(os.path.join(PROPS_DIR, 'apple_whole.png'), 'PNG')

    # 2. Shared Half Apples
    for name, flip in [('apple_half_chintu.png', False), ('apple_half_golu.png', True)]:
        him = Image.new('RGBA', (180, 220), (0, 0, 0, 0))
        hdraw = ImageDraw.Draw(him)
        # Rind arc
        hdraw.pieslice([10, 30, 160, 190], start=90 if not flip else 270, end=270 if not flip else 90, fill=apple_red, outline=apple_dark, width=3)
        # Flesh
        hdraw.pieslice([18, 38, 152, 182], start=90 if not flip else 270, end=270 if not flip else 90, fill=(255, 253, 231, 255))
        # Core & seed
        hdraw.ellipse([75, 95, 95, 125], fill=(215, 204, 180, 255))
        hdraw.ellipse([82, 105, 88, 115], fill=(93, 64, 55, 255))
        him.save(os.path.join(PROPS_DIR, name), 'PNG')

    # 3. Golden Star Sparkle
    sim = Image.new('RGBA', (120, 120), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(sim)
    cx, cy = 60, 60
    # Soft glow
    for r in range(45, 10, -4):
        draw_circle(sdraw, (cx, cy), r, fill=(255, 235, 59, int(15 + (45-r)*3)))
    # 4-point sparkle diamond
    sdraw.polygon([(cx, cy - 45), (cx + 12, cy - 8), (cx + 45, cy), (cx + 12, cy + 8),
                   (cx, cy + 45), (cx - 12, cy + 8), (cx - 45, cy), (cx - 12, cy - 8)],
                  fill=(255, 255, 255, 255), outline=(255, 215, 0, 255), width=2)
    sim.save(os.path.join(PROPS_DIR, 'sparkle_gold.png'), 'PNG')

    # 4. Colorful Musical Note
    nim = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    ndraw = ImageDraw.Draw(nim)
    ndraw.ellipse([20, 55, 45, 80], fill=(233, 30, 99, 255))
    ndraw.ellipse([60, 45, 85, 70], fill=(233, 30, 99, 255))
    ndraw.rectangle([40, 25, 46, 68], fill=(233, 30, 99, 255))
    ndraw.rectangle([80, 15, 86, 58], fill=(233, 30, 99, 255))
    ndraw.polygon([(40, 20), (86, 10), (86, 24), (40, 34)], fill=(233, 30, 99, 255))
    nim.save(os.path.join(PROPS_DIR, 'music_note.png'), 'PNG')

    print('Generated all props.')

def generate_chintu_rabbit_parts():
    # 1. Chintu Body (White fur with cute teal overalls)
    w, h = 300, 340
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Feet
    draw.ellipse([80, 280, 135, 325], fill=(245, 245, 245, 255), outline=(220, 220, 220, 255), width=3)
    draw.ellipse([165, 280, 220, 325], fill=(245, 245, 245, 255), outline=(220, 220, 220, 255), width=3)

    # Fluffy tail
    draw_circle(draw, (65, 250), 30, fill=(255, 255, 255, 255), outline=(225, 225, 225, 255), width=2)

    # Torso
    draw.ellipse([90, 90, 210, 270], fill=(255, 255, 255, 255), outline=(225, 225, 225, 255), width=3)

    # Teal Dungarees / Overalls
    teal = (0, 150, 136, 255)
    teal_dark = (0, 121, 107, 255)
    draw.pieslice([88, 130, 212, 290], start=0, end=180, fill=teal, outline=teal_dark, width=3)
    draw.rectangle([100, 180, 200, 280], fill=teal)
    # Straps
    draw.polygon([(105, 120), (125, 120), (120, 200), (100, 200)], fill=teal)
    draw.polygon([(175, 120), (195, 120), (200, 200), (180, 200)], fill=teal)
    # Yellow Buttons
    draw_circle(draw, (110, 195), 6, fill=(255, 235, 59, 255), outline=(255, 193, 7, 255), width=2)
    draw_circle(draw, (190, 195), 6, fill=(255, 235, 59, 255), outline=(255, 193, 7, 255), width=2)
    # Pocket with star
    draw.rectangle([130, 215, 170, 245], fill=(0, 121, 107, 255), outline=(0, 77, 64, 255), width=2)

    im.save(os.path.join(CHARACTERS_DIR, 'chintu_body.png'), 'PNG')

    # 2. Chintu Head
    hw, hh = 280, 240
    him = Image.new('RGBA', (hw, hh), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(him)

    # Chubby white bunny head
    hdraw.ellipse([40, 30, 240, 220], fill=(255, 255, 255, 255), outline=(225, 225, 225, 255), width=3)
    # Rosy Cheeks
    draw_circle(hdraw, (75, 155), 20, fill=(255, 182, 193, 160))
    draw_circle(hdraw, (205, 155), 20, fill=(255, 182, 193, 160))
    # Cute little pink triangle nose
    hdraw.polygon([(135, 140), (145, 140), (140, 148)], fill=(233, 30, 99, 255))
    # Whiskers
    hdraw.line([(55, 148), (25, 142)], fill=(180, 180, 180, 255), width=2)
    hdraw.line([(55, 158), (20, 162)], fill=(180, 180, 180, 255), width=2)
    hdraw.line([(225, 148), (255, 142)], fill=(180, 180, 180, 255), width=2)
    hdraw.line([(225, 158), (260, 162)], fill=(180, 180, 180, 255), width=2)

    him.save(os.path.join(CHARACTERS_DIR, 'chintu_head.png'), 'PNG')

    # 3. Chintu Ears (Left and Right)
    ew, eh = 90, 200
    eim = Image.new('RGBA', (ew, eh), (0, 0, 0, 0))
    edraw = ImageDraw.Draw(eim)
    edraw.ellipse([15, 10, 75, 190], fill=(255, 255, 255, 255), outline=(225, 225, 225, 255), width=3)
    edraw.ellipse([30, 35, 60, 165], fill=(255, 192, 203, 220))
    eim.save(os.path.join(CHARACTERS_DIR, 'chintu_ear.png'), 'PNG')

    # 4. Chintu Eyes
    for state in ['open', 'blink', 'happy', 'wide']:
        eyew, eyeh = 70, 70
        eyim = Image.new('RGBA', (eyew, eyeh), (0, 0, 0, 0))
        eydraw = ImageDraw.Draw(eyim)
        if state == 'open':
            eydraw.ellipse([12, 10, 58, 60], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=3)
            # Blue iris & pupil
            draw_circle(eydraw, (35, 36), 16, fill=(33, 150, 243, 255))
            draw_circle(eydraw, (35, 36), 11, fill=(20, 20, 20, 255))
            # Catchlight
            draw_circle(eydraw, (31, 30), 5, fill=(255, 255, 255, 255))
            draw_circle(eydraw, (39, 41), 2, fill=(255, 255, 255, 255))
        elif state == 'blink':
            eydraw.arc([10, 20, 60, 48], start=0, end=180, fill=(40, 40, 40, 255), width=4)
        elif state == 'happy':
            eydraw.arc([10, 15, 60, 48], start=180, end=360, fill=(40, 40, 40, 255), width=4)
        elif state == 'wide':
            eydraw.ellipse([6, 6, 64, 64], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=3)
            draw_circle(eydraw, (35, 35), 20, fill=(33, 150, 243, 255))
            draw_circle(eydraw, (35, 35), 14, fill=(10, 10, 10, 255))
            draw_circle(eydraw, (30, 27), 7, fill=(255, 255, 255, 255))
        eyim.save(os.path.join(CHARACTERS_DIR, f'chintu_eye_{state}.png'), 'PNG')

    # 5. Chintu Mouths (Visemes for Lip-Sync)
    for viseme in ['smile', 'open_a', 'open_o', 'wide_e']:
        mw, mh = 80, 60
        mim = Image.new('RGBA', (mw, mh), (0, 0, 0, 0))
        mdraw = ImageDraw.Draw(mim)
        if viseme == 'smile':
            mdraw.arc([15, 10, 65, 45], start=0, end=180, fill=(40, 40, 40, 255), width=3)
            # Two buckteeth
            mdraw.rectangle([34, 28, 40, 38], fill=(255, 255, 255, 255), outline=(60, 60, 60, 255), width=1)
            mdraw.rectangle([40, 28, 46, 38], fill=(255, 255, 255, 255), outline=(60, 60, 60, 255), width=1)
        elif viseme == 'open_a':
            mdraw.pieslice([15, 12, 65, 52], start=0, end=180, fill=(183, 28, 28, 255), outline=(40, 40, 40, 255), width=3)
            # Tongue
            mdraw.pieslice([24, 32, 56, 50], start=0, end=180, fill=(244, 143, 177, 255))
            # Teeth
            mdraw.rectangle([34, 13, 46, 22], fill=(255, 255, 255, 255))
        elif viseme == 'open_o':
            mdraw.ellipse([25, 10, 55, 48], fill=(183, 28, 28, 255), outline=(40, 40, 40, 255), width=3)
            mdraw.ellipse([30, 26, 50, 44], fill=(244, 143, 177, 255))
        elif viseme == 'wide_e':
            mdraw.pieslice([10, 8, 70, 50], start=0, end=180, fill=(183, 28, 28, 255), outline=(40, 40, 40, 255), width=3)
            mdraw.rectangle([25, 9, 55, 18], fill=(255, 255, 255, 255))
            mdraw.pieslice([22, 28, 58, 48], start=0, end=180, fill=(244, 143, 177, 255))
        mim.save(os.path.join(CHARACTERS_DIR, f'chintu_mouth_{viseme}.png'), 'PNG')

    # 6. Chintu Arms
    aw, ah = 60, 110
    aim = Image.new('RGBA', (aw, ah), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(aim)
    adraw.ellipse([10, 10, 50, 95], fill=(255, 255, 255, 255), outline=(225, 225, 225, 255), width=3)
    draw_circle(adraw, (30, 85), 18, fill=(255, 255, 255, 255), outline=(225, 225, 225, 255), width=2)
    aim.save(os.path.join(CHARACTERS_DIR, 'chintu_arm.png'), 'PNG')

    print('Generated all Chintu Rabbit character components.')

def generate_golu_bear_parts():
    # 1. Golu Bear Body
    w, h = 340, 360
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    bear_brown = (141, 110, 99, 255)
    bear_dark = (109, 76, 65, 255)
    cream_tummy = (239, 235, 233, 255)

    # Feet
    draw.ellipse([90, 290, 150, 345], fill=bear_brown, outline=bear_dark, width=3)
    draw.ellipse([190, 290, 250, 345], fill=bear_brown, outline=bear_dark, width=3)

    # Chubby Bear Torso
    draw.ellipse([85, 90, 255, 305], fill=bear_brown, outline=bear_dark, width=4)
    # Cream Tummy
    draw.ellipse([120, 140, 220, 275], fill=cream_tummy)

    # Cozy Yellow Scarf
    yellow_scarf = (255, 213, 79, 255)
    draw.pieslice([90, 75, 250, 135], start=0, end=180, fill=yellow_scarf, outline=(245, 124, 0, 255), width=3)
    # Scarf tail
    draw.polygon([(185, 105), (210, 105), (205, 175), (180, 175)], fill=yellow_scarf, outline=(245, 124, 0, 255), width=2)

    im.save(os.path.join(CHARACTERS_DIR, 'golu_body.png'), 'PNG')

    # 2. Golu Bear Head
    hw, hh = 300, 260
    him = Image.new('RGBA', (hw, hh), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(him)

    # Round bear ears
    draw_circle(hdraw, (75, 65), 42, fill=bear_brown, outline=bear_dark, width=3)
    draw_circle(hdraw, (75, 65), 24, fill=(215, 180, 170, 255))
    draw_circle(hdraw, (225, 65), 42, fill=bear_brown, outline=bear_dark, width=3)
    draw_circle(hdraw, (225, 65), 24, fill=(215, 180, 170, 255))

    # Chubby bear head
    hdraw.ellipse([45, 45, 255, 235], fill=bear_brown, outline=bear_dark, width=4)

    # Cream Muzzle
    hdraw.ellipse([95, 115, 205, 215], fill=cream_tummy, outline=(215, 204, 200, 255), width=2)
    # Soft Pink Cheeks
    draw_circle(hdraw, (75, 155), 18, fill=(255, 171, 145, 150))
    draw_circle(hdraw, (225, 155), 18, fill=(255, 171, 145, 150))
    # Dark bear nose
    hdraw.ellipse([132, 132, 168, 158], fill=(62, 39, 35, 255))
    draw_circle(hdraw, (144, 140), 4, fill=(255, 255, 255, 200))

    him.save(os.path.join(CHARACTERS_DIR, 'golu_head.png'), 'PNG')

    # 3. Golu Eyes
    for state in ['open', 'blink', 'happy', 'sad']:
        eyew, eyeh = 60, 60
        eyim = Image.new('RGBA', (eyew, eyeh), (0, 0, 0, 0))
        eydraw = ImageDraw.Draw(eyim)
        if state == 'open':
            eydraw.ellipse([12, 10, 48, 50], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=2)
            draw_circle(eydraw, (30, 30), 12, fill=(93, 64, 55, 255))
            draw_circle(eydraw, (30, 30), 8, fill=(20, 20, 20, 255))
            draw_circle(eydraw, (26, 26), 4, fill=(255, 255, 255, 255))
        elif state == 'blink':
            eydraw.arc([10, 18, 50, 42], start=0, end=180, fill=(40, 40, 40, 255), width=4)
        elif state == 'happy':
            eydraw.arc([10, 15, 50, 42], start=180, end=360, fill=(40, 40, 40, 255), width=4)
        elif state == 'sad':
            # Downturned sad eyes
            eydraw.ellipse([12, 12, 48, 48], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=2)
            draw_circle(eydraw, (30, 34), 10, fill=(93, 64, 55, 255))
            eydraw.line([(10, 14), (32, 22)], fill=(60, 60, 60, 255), width=3)
        eyim.save(os.path.join(CHARACTERS_DIR, f'golu_eye_{state}.png'), 'PNG')

    # 4. Golu Mouths
    for viseme in ['smile', 'sad', 'open_a', 'wide_e']:
        mw, mh = 70, 50
        mim = Image.new('RGBA', (mw, mh), (0, 0, 0, 0))
        mdraw = ImageDraw.Draw(mim)
        if viseme == 'smile':
            mdraw.arc([15, 10, 55, 38], start=0, end=180, fill=(62, 39, 35, 255), width=3)
        elif viseme == 'sad':
            mdraw.arc([15, 20, 55, 48], start=180, end=360, fill=(62, 39, 35, 255), width=3)
        elif viseme == 'open_a':
            mdraw.pieslice([16, 12, 54, 42], start=0, end=180, fill=(183, 28, 28, 255), outline=(62, 39, 35, 255), width=2)
            mdraw.pieslice([22, 26, 48, 40], start=0, end=180, fill=(244, 143, 177, 255))
        elif viseme == 'wide_e':
            mdraw.pieslice([12, 8, 58, 42], start=0, end=180, fill=(183, 28, 28, 255), outline=(62, 39, 35, 255), width=3)
            mdraw.pieslice([20, 22, 50, 40], start=0, end=180, fill=(244, 143, 177, 255))
        mim.save(os.path.join(CHARACTERS_DIR, f'golu_mouth_{viseme}.png'), 'PNG')

    # 5. Golu Arms
    aw, ah = 70, 120
    aim = Image.new('RGBA', (aw, ah), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(aim)
    adraw.ellipse([12, 10, 58, 105], fill=bear_brown, outline=bear_dark, width=3)
    draw_circle(adraw, (35, 95), 20, fill=bear_brown, outline=bear_dark, width=2)
    aim.save(os.path.join(CHARACTERS_DIR, 'golu_arm.png'), 'PNG')

    print('Generated all Golu Bear character components.')

if __name__ == '__main__':
    generate_background()
    generate_oak_tree()
    generate_props()
    generate_chintu_rabbit_parts()
    generate_golu_bear_parts()
    print('✅ ALL CARTOON ASSETS GENERATED SUCCESSFULLY!')
