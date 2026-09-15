import os
import sys
import math
sys.path.insert(0, r"C:\kids_automation")
from PIL import Image
from cartoon.config import CHARACTERS_DIR, PROPS_DIR

class CharacterRig:
    def __init__(self):
        self._load_assets()

    def _load_assets(self):
        self.c_body = Image.open(os.path.join(CHARACTERS_DIR, "chintu_body.png")).convert("RGBA")
        self.c_head = Image.open(os.path.join(CHARACTERS_DIR, "chintu_head.png")).convert("RGBA")
        self.c_ear = Image.open(os.path.join(CHARACTERS_DIR, "chintu_ear.png")).convert("RGBA")
        self.c_arm = Image.open(os.path.join(CHARACTERS_DIR, "chintu_arm.png")).convert("RGBA")

        self.c_eyes = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"chintu_eye_{s}.png")).convert("RGBA")
            for s in ["open", "blink", "happy", "wide"]
        }
        self.c_mouths = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"chintu_mouth_{s}.png")).convert("RGBA")
            for s in ["smile", "open_a", "open_o", "wide_e"]
        }

        self.g_body = Image.open(os.path.join(CHARACTERS_DIR, "golu_body.png")).convert("RGBA")
        self.g_head = Image.open(os.path.join(CHARACTERS_DIR, "golu_head.png")).convert("RGBA")
        self.g_arm = Image.open(os.path.join(CHARACTERS_DIR, "golu_arm.png")).convert("RGBA")

        self.g_eyes = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"golu_eye_{s}.png")).convert("RGBA")
            for s in ["open", "blink", "happy", "sad"]
        }
        self.g_mouths = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"golu_mouth_{s}.png")).convert("RGBA")
            for s in ["smile", "sad", "open_a", "wide_e"]
        }

        self.props = {
            "apple_whole": Image.open(os.path.join(PROPS_DIR, "apple_whole.png")).convert("RGBA"),
            "apple_half_chintu": Image.open(os.path.join(PROPS_DIR, "apple_half_chintu.png")).convert("RGBA"),
            "apple_half_golu": Image.open(os.path.join(PROPS_DIR, "apple_half_golu.png")).convert("RGBA"),
            "sparkle": Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA"),
            "music_note": Image.open(os.path.join(PROPS_DIR, "music_note.png")).convert("RGBA"),
        }

        # Variety characters: Koko (squirrel), Bholu (puppy), Leo (lion cub)
        koko_body_p = os.path.join(CHARACTERS_DIR, "koko_body.png")
        if os.path.exists(koko_body_p):
            self.koko_body = Image.open(koko_body_p).convert("RGBA")
            self.koko_head = Image.open(os.path.join(CHARACTERS_DIR, "koko_head.png")).convert("RGBA")
            self.koko_ear = Image.open(os.path.join(CHARACTERS_DIR, "koko_ear.png")).convert("RGBA")
            self.koko_arm = Image.open(os.path.join(CHARACTERS_DIR, "koko_arm.png")).convert("RGBA")
            self.koko_tail = Image.open(os.path.join(CHARACTERS_DIR, "koko_tail.png")).convert("RGBA")

        bholu_body_p = os.path.join(CHARACTERS_DIR, "bholu_body.png")
        if os.path.exists(bholu_body_p):
            self.bholu_body = Image.open(bholu_body_p).convert("RGBA")
            self.bholu_head = Image.open(os.path.join(CHARACTERS_DIR, "bholu_head.png")).convert("RGBA")
            self.bholu_ear = Image.open(os.path.join(CHARACTERS_DIR, "bholu_ear.png")).convert("RGBA")
            self.bholu_arm = Image.open(os.path.join(CHARACTERS_DIR, "bholu_arm.png")).convert("RGBA")

        leo_body_p = os.path.join(CHARACTERS_DIR, "leo_body.png")
        if os.path.exists(leo_body_p):
            self.leo_body = Image.open(leo_body_p).convert("RGBA")
            self.leo_head = Image.open(os.path.join(CHARACTERS_DIR, "leo_head.png")).convert("RGBA")
            self.leo_ear = Image.open(os.path.join(CHARACTERS_DIR, "leo_ear.png")).convert("RGBA")
            self.leo_arm = Image.open(os.path.join(CHARACTERS_DIR, "leo_arm.png")).convert("RGBA")

    def render_chintu(self, t, action="idle", eye_state=None, mouth_state="smile",
                      held_item=None, facing=1, scale=1.0, is_speaking=False):
        canvas_w, canvas_h = 420, 520
        im = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        bounce = 0.0
        ear_sway = 0.0
        arm_l_rot = 0.0
        arm_r_rot = 0.0

        if action == "hop":
            cycle = (t * 4.5) % (2 * math.pi)
            bounce = abs(math.sin(cycle)) * 42.0
            ear_sway = math.sin(cycle - 0.4) * 14.0
            arm_l_rot = math.sin(cycle) * 25.0
            arm_r_rot = -math.sin(cycle) * 25.0
        elif action == "celebrate":
            cycle = (t * 6.0) % (2 * math.pi)
            bounce = abs(math.sin(cycle)) * 28.0
            ear_sway = math.sin(cycle * 1.5) * 18.0
            arm_l_rot = -120 + math.sin(cycle * 2) * 20.0
            arm_r_rot = -120 - math.sin(cycle * 2) * 20.0
        elif action == "give":
            bounce = math.sin(t * 2.0) * 4.0
            ear_sway = 4.0
            arm_r_rot = -65.0
        elif action == "hold":
            bounce = math.sin(t * 2.0) * 5.0
            arm_r_rot = -45.0
            arm_l_rot = -45.0
        elif action == "wave":
            bounce = math.sin(t * 2.5) * 6.0
            arm_l_rot = -110 + math.sin(t * 8.0) * 25.0
        else:  # idle
            bounce = math.sin(t * 2.0) * 6.0
            ear_sway = math.sin(t * 1.5) * 4.0

        if eye_state is None:
            blink_cycle = t % 3.2
            eye_state = "blink" if 2.95 <= blink_cycle <= 3.12 else "open"

        if is_speaking:
            phoneme_idx = int(t * 8.0) % 4
            mouth_state = ["open_a", "wide_e", "open_o", "open_a"][phoneme_idx]

        # 1. Back Ear
        ear_l = self.c_ear.rotate(ear_sway - 8, resample=Image.Resampling.BICUBIC, center=(45, 180))
        im.alpha_composite(ear_l, (130, int(30 - bounce)))

        # 2. Body
        im.alpha_composite(self.c_body, (60, int(170 - bounce)))

        # 3. Front Ear
        ear_r = self.c_ear.rotate(-ear_sway + 10, resample=Image.Resampling.BICUBIC, center=(45, 180))
        im.alpha_composite(ear_r, (185, int(25 - bounce)))

        # 4. Head
        im.alpha_composite(self.c_head, (70, int(60 - bounce)))

        # 5. Eyes
        ey = self.c_eyes.get(eye_state, self.c_eyes["open"])
        im.alpha_composite(ey, (115, int(135 - bounce)))
        im.alpha_composite(ey, (180, int(135 - bounce)))

        # 6. Mouth
        m = self.c_mouths.get(mouth_state, self.c_mouths["smile"])
        im.alpha_composite(m, (145, int(195 - bounce)))

        # 7. Left Arm
        arm_l = self.c_arm.rotate(arm_l_rot, resample=Image.Resampling.BICUBIC, center=(30, 20))
        im.alpha_composite(arm_l, (80, int(210 - bounce)))

        # 8. Right Arm
        arm_r = self.c_arm.rotate(arm_r_rot, resample=Image.Resampling.BICUBIC, center=(30, 20))
        im.alpha_composite(arm_r, (230, int(210 - bounce)))

        # 9. Held Item
        if held_item and held_item in self.props:
            prop = self.props[held_item]
            if held_item == "apple_whole":
                prop_scaled = prop.resize((110, 110), Image.Resampling.LANCZOS)
                px = 250 if action == "give" else 190
                py = int(220 - bounce)
                im.alpha_composite(prop_scaled, (px, py))
            elif "apple_half" in held_item:
                prop_scaled = prop.resize((85, 100), Image.Resampling.LANCZOS)
                px = 240 if action == "give" else 180
                py = int(230 - bounce)
                im.alpha_composite(prop_scaled, (px, py))

        if facing < 0:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if scale != 1.0:
            nw = int(canvas_w * scale)
            nh = int(canvas_h * scale)
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)

        return im

    def render_golu(self, t, action="idle", eye_state=None, mouth_state="smile",
                    held_item=None, facing=-1, scale=1.0, is_speaking=False):
        canvas_w, canvas_h = 440, 520
        im = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        bounce = 0.0
        arm_l_rot = 0.0
        arm_r_rot = 0.0

        if action == "sad_idle":
            bounce = math.sin(t * 1.5) * 4.0
            arm_l_rot = 20.0
            arm_r_rot = -20.0
            if eye_state is None:
                eye_state = "sad"
            if mouth_state == "smile":
                mouth_state = "sad"
        elif action == "celebrate":
            cycle = (t * 5.5) % (2 * math.pi)
            bounce = abs(math.sin(cycle)) * 26.0
            arm_l_rot = -115 + math.sin(cycle * 2) * 18.0
            arm_r_rot = -115 - math.sin(cycle * 2) * 18.0
            eye_state = "happy"
            mouth_state = "wide_e"
        elif action == "receive":
            bounce = math.sin(t * 2.0) * 5.0
            arm_l_rot = -55.0
            arm_r_rot = -30.0
            eye_state = "happy"
        elif action == "wave":
            bounce = math.sin(t * 2.5) * 6.0
            arm_r_rot = -110 + math.sin(t * 7.5) * 25.0
        else:  # normal idle / walk
            cycle = (t * 3.0) % (2 * math.pi)
            bounce = math.sin(cycle) * 8.0
            arm_l_rot = math.sin(cycle) * 15.0
            arm_r_rot = -math.sin(cycle) * 15.0

        if eye_state is None:
            blink_cycle = (t + 1.2) % 3.4
            eye_state = "blink" if 3.1 <= blink_cycle <= 3.3 else "open"

        if is_speaking:
            phoneme_idx = int(t * 7.5) % 3
            mouth_state = ["open_a", "wide_e", "open_a"][phoneme_idx]

        # 1. Body
        im.alpha_composite(self.g_body, (50, int(160 - bounce)))

        # 2. Head
        im.alpha_composite(self.g_head, (70, int(70 - bounce)))

        # 3. Eyes
        ey = self.g_eyes.get(eye_state, self.g_eyes["open"])
        im.alpha_composite(ey, (115, int(140 - bounce)))
        im.alpha_composite(ey, (190, int(140 - bounce)))

        # 4. Mouth
        m = self.g_mouths.get(mouth_state, self.g_mouths["smile"])
        im.alpha_composite(m, (145, int(195 - bounce)))

        # 5. Left Arm
        arm_l = self.g_arm.rotate(arm_l_rot, resample=Image.Resampling.BICUBIC, center=(35, 20))
        im.alpha_composite(arm_l, (65, int(200 - bounce)))

        # 6. Right Arm
        arm_r = self.g_arm.rotate(arm_r_rot, resample=Image.Resampling.BICUBIC, center=(35, 20))
        im.alpha_composite(arm_r, (275, int(200 - bounce)))

        # 7. Held Item
        if held_item and held_item in self.props:
            prop = self.props[held_item]
            prop_scaled = prop.resize((85, 100), Image.Resampling.LANCZOS)
            px = 120 if facing < 0 else 230
            py = int(220 - bounce)
            im.alpha_composite(prop_scaled, (px, py))

        if facing < 0:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if scale != 1.0:
            nw = int(canvas_w * scale)
            nh = int(canvas_h * scale)
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)

        return im

    def render_character(self, char_name, t, action="idle", eye_state=None, mouth_state="smile",
                         held_item=None, facing=1, scale=1.0, is_speaking=False):
        """
        Renders any V1 character dynamically (Chintu Bunny, Koko Squirrel,
        Bholu Puppy, Leo Lion Cub, Golu Bear).
        """
        c_norm = (char_name or "").strip().lower()
        if c_norm == "golu":
            return self.render_golu(t, action=action, eye_state=eye_state, mouth_state=mouth_state,
                                    held_item=held_item, facing=facing, scale=scale, is_speaking=is_speaking)

        if c_norm not in ("koko", "bholu", "leo"):
            return self.render_chintu(t, action=action, eye_state=eye_state, mouth_state=mouth_state,
                                     held_item=held_item, facing=facing, scale=scale, is_speaking=is_speaking)

        # Select sprites based on character
        if c_norm == "koko" and hasattr(self, "koko_body"):
            body_img = self.koko_body
            head_img = self.koko_head
            ear_img = self.koko_ear
            arm_img = self.koko_arm
            tail_img = getattr(self, "koko_tail", None)
        elif c_norm == "bholu" and hasattr(self, "bholu_body"):
            body_img = self.bholu_body
            head_img = self.bholu_head
            ear_img = self.bholu_ear
            arm_img = self.bholu_arm
            tail_img = None
        elif c_norm == "leo" and hasattr(self, "leo_body"):
            body_img = self.leo_body
            head_img = self.leo_head
            ear_img = self.leo_ear
            arm_img = self.leo_arm
            tail_img = None
        else:
            return self.render_chintu(t, action=action, eye_state=eye_state, mouth_state=mouth_state,
                                     held_item=held_item, facing=facing, scale=scale, is_speaking=is_speaking)

        canvas_w, canvas_h = 420, 520
        im = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        bounce = 0.0
        ear_sway = 0.0
        arm_l_rot = 0.0
        arm_r_rot = 0.0

        if action == "hop":
            cycle = (t * 4.5) % (2 * math.pi)
            bounce = abs(math.sin(cycle)) * 38.0
            ear_sway = math.sin(cycle - 0.4) * 12.0
            arm_l_rot = math.sin(cycle) * 22.0
            arm_r_rot = -math.sin(cycle) * 22.0
        elif action == "celebrate":
            cycle = (t * 6.0) % (2 * math.pi)
            bounce = abs(math.sin(cycle)) * 26.0
            ear_sway = math.sin(cycle * 1.5) * 15.0
            arm_l_rot = -115 + math.sin(cycle * 2) * 18.0
            arm_r_rot = -115 - math.sin(cycle * 2) * 18.0
        elif action == "give":
            bounce = math.sin(t * 2.0) * 4.0
            ear_sway = 4.0
            arm_r_rot = -65.0
        elif action == "hold":
            bounce = math.sin(t * 2.0) * 5.0
            arm_r_rot = -45.0
            arm_l_rot = -45.0
        elif action == "wave":
            bounce = math.sin(t * 2.5) * 6.0
            arm_l_rot = -110 + math.sin(t * 8.0) * 25.0
        else:  # idle
            bounce = math.sin(t * 2.0) * 5.0
            ear_sway = math.sin(t * 1.5) * 3.0

        if eye_state is None:
            blink_cycle = t % 3.2
            eye_state = "blink" if 2.95 <= blink_cycle <= 3.12 else "open"

        if is_speaking:
            phoneme_idx = int(t * 8.0) % 4
            mouth_state = ["open_a", "wide_e", "open_o", "open_a"][phoneme_idx]

        # 0. Tail (if squirrel)
        if tail_img:
            tail_sway = math.sin(t * 3.5) * 8.0
            rot_tail = tail_img.rotate(tail_sway, resample=Image.Resampling.BICUBIC)
            im.alpha_composite(rot_tail, (10, int(150 - bounce)))

        # 1. Back Ear
        ear_l = ear_img.rotate(ear_sway - 6, resample=Image.Resampling.BICUBIC, center=(45, 180))
        im.alpha_composite(ear_l, (130, int(35 - bounce)))

        # 2. Body
        im.alpha_composite(body_img, (60, int(170 - bounce)))

        # 3. Front Ear
        ear_r = ear_img.rotate(-ear_sway + 8, resample=Image.Resampling.BICUBIC, center=(45, 180))
        im.alpha_composite(ear_r, (185, int(30 - bounce)))

        # 4. Head
        im.alpha_composite(head_img, (70, int(65 - bounce)))

        # 5. Eyes
        ey = self.c_eyes.get(eye_state, self.c_eyes["open"])
        im.alpha_composite(ey, (115, int(140 - bounce)))
        im.alpha_composite(ey, (180, int(140 - bounce)))

        # 6. Mouth
        m = self.c_mouths.get(mouth_state, self.c_mouths["smile"])
        im.alpha_composite(m, (145, int(198 - bounce)))

        # 7. Arms
        arm_l = arm_img.rotate(arm_l_rot, resample=Image.Resampling.BICUBIC, center=(30, 20))
        im.alpha_composite(arm_l, (80, int(210 - bounce)))

        arm_r = arm_img.rotate(arm_r_rot, resample=Image.Resampling.BICUBIC, center=(30, 20))
        im.alpha_composite(arm_r, (230, int(210 - bounce)))

        if held_item and held_item in self.props:
            prop = self.props[held_item]
            prop_scaled = prop.resize((90, 90), Image.Resampling.LANCZOS)
            px = 240 if action == "give" else 185
            py = int(225 - bounce)
            im.alpha_composite(prop_scaled, (px, py))

        if facing < 0:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if scale != 1.0:
            nw = int(canvas_w * scale)
            nh = int(canvas_h * scale)
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)

        return im
