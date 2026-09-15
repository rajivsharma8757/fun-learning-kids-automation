"""
character_rig_v2.py
--------------------
Advanced 2D Skeletal Kinematic Character Rig for "Fun Learning Kids" Cartoon Module.
Implements:
- Hierarchical body parts: Head, Torso, Ears/Scarf, Articulated Upper & Lower Arms,
  Articulated Upper & Lower Legs (with feet & knees), Tail.
- Organic Squash & Stretch deformation.
- True kinematic cycles: Bipedal walking with counter-balancing arms, multi-phase hopping
  (anticipation crouch -> stretch leap -> apex -> landing squash -> settle),
  reaching, grasping, holding, giving, receiving, chewing/munching, and waving.
- Look-at eye tracking, dynamic eyebrows, and 7 speech visemes.
"""

import os
import sys
import math
from PIL import Image, ImageDraw

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CHARACTERS_DIR, PROPS_DIR


def ease_in_out_quad(t):
    return 2 * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 2) / 2


def ease_out_bounce(t):
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


class CharacterRigV2:
    def __init__(self):
        self._load_assets()

    def _load_assets(self):
        # 1. Chintu Bunny Assets
        self.c_head = Image.open(os.path.join(CHARACTERS_DIR, "chintu_head.png")).convert("RGBA")
        self.c_torso = Image.open(os.path.join(CHARACTERS_DIR, "chintu_torso.png")).convert("RGBA")
        self.c_ear_l = Image.open(os.path.join(CHARACTERS_DIR, "chintu_ear_l.png")).convert("RGBA")
        self.c_ear_r = Image.open(os.path.join(CHARACTERS_DIR, "chintu_ear_r.png")).convert("RGBA")
        self.c_arm_u = Image.open(os.path.join(CHARACTERS_DIR, "chintu_arm_upper.png")).convert("RGBA")
        self.c_arm_l = Image.open(os.path.join(CHARACTERS_DIR, "chintu_arm_lower.png")).convert("RGBA")
        self.c_leg_u = Image.open(os.path.join(CHARACTERS_DIR, "chintu_leg_upper.png")).convert("RGBA")
        self.c_leg_l = Image.open(os.path.join(CHARACTERS_DIR, "chintu_leg_lower.png")).convert("RGBA")
        self.c_tail = Image.open(os.path.join(CHARACTERS_DIR, "chintu_tail.png")).convert("RGBA")

        self.c_eyes = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"chintu_eye_{s}.png")).convert("RGBA")
            for s in ["open", "blink", "happy", "wide", "look_down", "look_right"]
        }
        self.c_brows = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"chintu_brow_{s}.png")).convert("RGBA")
            for s in ["neutral", "happy", "curious", "surprised"]
        }
        self.c_mouths = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"chintu_mouth_{s}.png")).convert("RGBA")
            for s in ["closed", "smile", "open_ah", "wide_ee", "round_oh", "pout_oo", "munch_crunch"]
        }

        # 2. Golu Bear Assets
        self.g_head = Image.open(os.path.join(CHARACTERS_DIR, "golu_head.png")).convert("RGBA")
        self.g_torso = Image.open(os.path.join(CHARACTERS_DIR, "golu_torso.png")).convert("RGBA")
        self.g_scarf = Image.open(os.path.join(CHARACTERS_DIR, "golu_scarf.png")).convert("RGBA")
        self.g_arm_u = Image.open(os.path.join(CHARACTERS_DIR, "golu_arm_upper.png")).convert("RGBA")
        self.g_arm_l = Image.open(os.path.join(CHARACTERS_DIR, "golu_arm_lower.png")).convert("RGBA")
        self.g_leg_u = Image.open(os.path.join(CHARACTERS_DIR, "golu_leg_upper.png")).convert("RGBA")
        self.g_leg_l = Image.open(os.path.join(CHARACTERS_DIR, "golu_leg_lower.png")).convert("RGBA")

        self.g_eyes = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"golu_eye_{s}.png")).convert("RGBA")
            for s in ["open", "blink", "happy", "sad", "surprised", "look_down"]
        }
        self.g_brows = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"golu_brow_{s}.png")).convert("RGBA")
            for s in ["neutral", "sad", "happy", "surprised"]
        }
        self.g_mouths = {
            s: Image.open(os.path.join(CHARACTERS_DIR, f"golu_mouth_{s}.png")).convert("RGBA")
            for s in ["smile", "sad", "open_ah", "wide_ee", "round_oh", "munch_crunch"]
        }

        # 3. Interactive Props
        self.props = {
            "apple_whole": Image.open(os.path.join(PROPS_DIR, "apple_whole.png")).convert("RGBA"),
            "apple_half_chintu": Image.open(os.path.join(PROPS_DIR, "apple_half_chintu.png")).convert("RGBA"),
            "apple_half_golu": Image.open(os.path.join(PROPS_DIR, "apple_half_golu.png")).convert("RGBA"),
            "apple_bitten_chintu": Image.open(os.path.join(PROPS_DIR, "apple_bitten_chintu.png")).convert("RGBA"),
            "apple_bitten_golu": Image.open(os.path.join(PROPS_DIR, "apple_bitten_golu.png")).convert("RGBA"),
            "sparkle": Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA"),
            "music_note": Image.open(os.path.join(PROPS_DIR, "music_note.png")).convert("RGBA"),
        }

    # =========================================================================
    # CHINTU BUNNY KINEMATIC RENDERING
    # =========================================================================
    def render_chintu(
        self, t, action="idle", action_progress=0.0,
        eye_state=None, brow_state="happy", mouth_state=None,
        held_item=None, facing=1, scale=1.0, is_speaking=False
    ):
        """
        Renders fully articulated Chintu with realistic 2D skeletal poses,
        squash & stretch, independent legs/arms/ears/head.
        """
        canvas_w, canvas_h = 480, 560
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        # Default kinematic parameters
        y_offset = 0.0
        squash_y = 1.0
        squash_x = 1.0
        head_tilt = 0.0
        ear_sway = 0.0

        arm_l_u_rot, arm_l_l_rot = 15.0, 10.0
        arm_r_u_rot, arm_r_l_rot = -15.0, -10.0

        leg_l_u_rot, leg_l_l_rot = 0.0, 0.0
        leg_r_u_rot, leg_r_l_rot = 0.0, 0.0

        # Action Kinematics Computation
        if action == "hop":
            # True multi-phase hop with squash, explosion, apex, landing
            cycle = (t * 5.0) % 1.0  # 0.0 to 1.0 per hop
            if cycle < 0.20:
                # 1. Anticipation / Deep Crouch
                p = cycle / 0.20
                squash_y = 1.0 - 0.22 * math.sin(p * math.pi)
                squash_x = 1.0 + 0.18 * math.sin(p * math.pi)
                y_offset = 24.0 * math.sin(p * math.pi)
                leg_l_u_rot, leg_l_l_rot = 35.0, -45.0
                leg_r_u_rot, leg_r_l_rot = 35.0, -45.0
                arm_l_u_rot, arm_r_u_rot = -35.0, -35.0
                ear_sway = -16.0
            elif cycle < 0.70:
                # 2. Airborne Leap & Stretch
                p = (cycle - 0.20) / 0.50
                arc = math.sin(p * math.pi)
                y_offset = -65.0 * arc
                squash_y = 1.0 + 0.18 * arc
                squash_x = 1.0 - 0.12 * arc
                leg_l_u_rot, leg_l_l_rot = -15.0, 15.0
                leg_r_u_rot, leg_r_l_rot = -20.0, 20.0
                arm_l_u_rot, arm_r_u_rot = -70.0, -70.0
                ear_sway = 22.0 * math.sin(p * math.pi * 1.5)
            else:
                # 3. Landing & Settle (Overshoot)
                p = (cycle - 0.70) / 0.30
                squash_y = 1.0 - 0.18 * (1.0 - p)
                squash_x = 1.0 + 0.14 * (1.0 - p)
                y_offset = 18.0 * (1.0 - p)
                leg_l_u_rot, leg_l_l_rot = 25.0 * (1.0 - p), -30.0 * (1.0 - p)
                leg_r_u_rot, leg_r_l_rot = 25.0 * (1.0 - p), -30.0 * (1.0 - p)
                ear_sway = -12.0 * (1.0 - p)

        elif action == "walk":
            # Alternating bipedal walk cycle
            cycle = (t * 4.5) % (2 * math.pi)
            leg_l_u_rot = math.sin(cycle) * 32.0
            leg_l_l_rot = max(0.0, -math.sin(cycle)) * 30.0
            leg_r_u_rot = -math.sin(cycle) * 32.0
            leg_r_l_rot = max(0.0, math.sin(cycle)) * 30.0

            # Counter-arm swing
            arm_l_u_rot = -math.sin(cycle) * 35.0
            arm_r_u_rot = math.sin(cycle) * 35.0
            y_offset = abs(math.sin(cycle)) * 8.0
            ear_sway = math.sin(cycle - 0.5) * 8.0
            head_tilt = -math.sin(cycle) * 4.0

        elif action == "crouch_and_reach":
            # Bending down to grasp apple
            p = min(1.0, max(0.0, action_progress))
            y_offset = 28.0 * p
            squash_y = 1.0 - 0.16 * p
            squash_x = 1.0 + 0.12 * p
            leg_l_u_rot, leg_l_l_rot = 40.0 * p, -50.0 * p
            leg_r_u_rot, leg_r_l_rot = 40.0 * p, -50.0 * p
            arm_r_u_rot = 65.0 * p   # Reaching down forward
            arm_r_l_rot = 25.0 * p
            head_tilt = 18.0 * p
            if eye_state is None:
                eye_state = "look_down"

        elif action == "hold_up":
            # Proudly holding apple high
            bob = math.sin(t * 3.0) * 4.0
            y_offset = bob
            arm_r_u_rot, arm_r_l_rot = -75.0, -45.0
            arm_l_u_rot, arm_l_l_rot = -75.0, -45.0
            head_tilt = -10.0
            ear_sway = math.sin(t * 2.0) * 6.0
            if eye_state is None:
                eye_state = "wide"

        elif action == "give":
            # Stepping forward and offering apple half to Golu
            p = min(1.0, max(0.0, action_progress))
            arm_r_u_rot = -55.0 - p * 20.0
            arm_r_l_rot = -25.0 - p * 15.0
            head_tilt = 8.0 * p
            leg_r_u_rot = 18.0 * p
            ear_sway = 6.0

        elif action == "munch":
            # Chewing apple half rhythmically
            chew = (t * 7.0) % (2 * math.pi)
            head_tilt = math.sin(chew) * 6.0
            arm_r_u_rot = -80.0 + math.sin(chew) * 6.0
            arm_r_l_rot = -50.0
            y_offset = abs(math.sin(chew)) * 5.0
            mouth_state = "munch_crunch" if math.sin(chew) > 0 else "closed"

        elif action == "wave":
            # Friendly wave to camera
            arm_r_u_rot = -120.0
            arm_r_l_rot = -30.0 + math.sin(t * 8.0) * 35.0
            head_tilt = math.sin(t * 3.0) * 6.0
            ear_sway = math.sin(t * 3.0) * 8.0
            y_offset = math.sin(t * 3.0) * 4.0

        else:  # Idle
            breathe = math.sin(t * 2.5)
            y_offset = breathe * 4.0
            squash_y = 1.0 + breathe * 0.03
            squash_x = 1.0 - breathe * 0.02
            ear_sway = math.sin(t * 2.0) * 5.0

        # Facial Expression & Lip-Sync
        if eye_state is None:
            blink_c = t % 3.4
            eye_state = "blink" if 3.15 <= blink_c <= 3.32 else "open"

        if is_speaking and mouth_state is None:
            # Dynamic speech viseme cadence
            v_idx = int(t * 9.0) % 5
            mouth_state = ["open_ah", "wide_ee", "round_oh", "smile", "open_ah"][v_idx]
        elif mouth_state is None:
            mouth_state = "smile"

        # ---------------------------------------------------------------------
        # SKELETAL COMPOSITING (Hierarchical Layer Order)
        # ---------------------------------------------------------------------
        center_x = canvas_w // 2
        hip_y = int(320 + y_offset)

        # 1. Back Tail
        canvas.alpha_composite(self.c_tail, (center_x - 110, hip_y + 10))

        # 2. Back (Left) Leg
        leg_l = self._render_limb(self.c_leg_u, self.c_leg_l, leg_l_u_rot, leg_l_l_rot, joint_offset=(20, 20))
        canvas.alpha_composite(leg_l, (center_x - 65, hip_y + 40))

        # 3. Back (Left) Arm
        arm_l = self._render_limb(self.c_arm_u, self.c_arm_l, arm_l_u_rot, arm_l_l_rot, joint_offset=(18, 18))
        canvas.alpha_composite(arm_l, (center_x - 90, hip_y - 85))

        # 4. Torso with Dungarees
        torso_w = int(self.c_torso.width * squash_x)
        torso_h = int(self.c_torso.height * squash_y)
        torso_sc = self.c_torso.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
        canvas.alpha_composite(torso_sc, (center_x - torso_w // 2, hip_y - 75))

        # 5. Front (Right) Leg
        leg_r = self._render_limb(self.c_leg_u, self.c_leg_l, leg_r_u_rot, leg_r_l_rot, joint_offset=(20, 20))
        canvas.alpha_composite(leg_r, (center_x - 15, hip_y + 45))

        # 6. Ears (attached to head with dynamic sway)
        head_cx = center_x
        head_cy = hip_y - 115
        ear_l_rot = self.c_ear_l.rotate(ear_sway - 8, resample=Image.Resampling.BICUBIC, center=(50, 200))
        canvas.alpha_composite(ear_l_rot, (head_cx - 95, head_cy - 165))
        ear_r_rot = self.c_ear_r.rotate(ear_sway + 8, resample=Image.Resampling.BICUBIC, center=(50, 200))
        canvas.alpha_composite(ear_r_rot, (head_cx - 5, head_cy - 165))

        # 7. Head (with facial expression)
        head_im = self.c_head.copy()
        # Eyes
        ey = self.c_eyes.get(eye_state, self.c_eyes["open"])
        head_im.alpha_composite(ey, (100, 115))
        head_im.alpha_composite(ey, (180, 115))
        # Eyebrows
        br = self.c_brows.get(brow_state, self.c_brows["happy"])
        head_im.alpha_composite(br, (100, 85))
        head_im.alpha_composite(br, (180, 85))
        # Mouth
        mo = self.c_mouths.get(mouth_state, self.c_mouths["smile"])
        head_im.alpha_composite(mo, (135, 200))

        head_rot = head_im.rotate(head_tilt, resample=Image.Resampling.BICUBIC, center=(170, 200))
        canvas.alpha_composite(head_rot, (head_cx - 170, head_cy - 120))

        # 8. Front (Right) Arm
        arm_r = self._render_limb(self.c_arm_u, self.c_arm_l, arm_r_u_rot, arm_r_l_rot, joint_offset=(18, 18))
        canvas.alpha_composite(arm_r, (center_x + 35, hip_y - 85))

        # 9. Held Prop (Apple Whole / Split Half / Bitten)
        if held_item and held_item in self.props:
            prop = self.props[held_item]
            if held_item == "apple_whole":
                prop_sc = prop.resize((120, 120), Image.Resampling.LANCZOS)
                px = center_x + (85 if action == "give" else 50)
                py = hip_y - (130 if action == "hold_up" else 40)
            else:
                prop_sc = prop.resize((95, 110), Image.Resampling.LANCZOS)
                px = center_x + (90 if action == "give" else 40)
                py = hip_y - (95 if action == "munch" else 35)
            canvas.alpha_composite(prop_sc, (px, py))

        # Flip horizontally if facing left
        if facing < 0:
            canvas = canvas.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Scale canvas if requested
        if scale != 1.0:
            nw = int(canvas_w * scale)
            nh = int(canvas_h * scale)
            canvas = canvas.resize((nw, nh), Image.Resampling.LANCZOS)

        return canvas

    # =========================================================================
    # GOLU BEAR KINEMATIC RENDERING
    # =========================================================================
    def render_golu(
        self, t, action="idle", action_progress=0.0,
        eye_state=None, brow_state="neutral", mouth_state=None,
        held_item=None, facing=-1, scale=1.0, is_speaking=False
    ):
        """
        Renders fully articulated Golu Bear with honey brown fur,
        knitted yellow scarf, chubby walk/sad/receive/munch/wave cycles.
        """
        canvas_w, canvas_h = 500, 580
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        y_offset = 0.0
        squash_y = 1.0
        squash_x = 1.0
        head_tilt = 0.0
        scarf_flutter = 0.0

        arm_l_u_rot, arm_l_l_rot = 15.0, 10.0
        arm_r_u_rot, arm_r_l_rot = -15.0, -10.0

        leg_l_u_rot, leg_l_l_rot = 0.0, 0.0
        leg_r_u_rot, leg_r_l_rot = 0.0, 0.0

        # Action Kinematics Computation
        if action == "walk_sad":
            # Slow sad walk holding rumbling tummy
            cycle = (t * 3.2) % (2 * math.pi)
            leg_l_u_rot = math.sin(cycle) * 25.0
            leg_r_u_rot = -math.sin(cycle) * 25.0
            # Both hands holding tummy
            arm_l_u_rot, arm_l_l_rot = 35.0, 45.0
            arm_r_u_rot, arm_r_l_rot = -35.0, -45.0
            y_offset = abs(math.sin(cycle)) * 6.0
            head_tilt = 12.0 + math.sin(cycle) * 4.0
            scarf_flutter = math.sin(cycle) * 8.0
            if eye_state is None:
                eye_state = "sad"
            if brow_state == "neutral":
                brow_state = "sad"
            if mouth_state is None:
                mouth_state = "sad"

        elif action == "receive":
            # Reaching out with joy and anticipation to accept the apple
            p = min(1.0, max(0.0, action_progress))
            arm_l_u_rot = -55.0 * p
            arm_l_l_rot = -35.0 * p
            arm_r_u_rot = 20.0
            head_tilt = -8.0 * p
            if p > 0.4:
                eye_state = "happy"
                brow_state = "happy"
                mouth_state = "smile"
            else:
                eye_state = "surprised"
                brow_state = "surprised"

        elif action == "munch":
            # Joyful celebration munching
            chew = (t * 6.5) % (2 * math.pi)
            head_tilt = math.sin(chew) * 7.0
            arm_l_u_rot = -75.0 + math.sin(chew) * 6.0
            arm_l_l_rot = -45.0
            y_offset = abs(math.sin(chew)) * 6.0
            mouth_state = "munch_crunch" if math.sin(chew) > 0 else "smile"
            eye_state = "happy"
            brow_state = "happy"

        elif action == "dance":
            # Joyful dance bounce
            cycle = (t * 5.0) % (2 * math.pi)
            y_offset = -20.0 * abs(math.sin(cycle))
            squash_y = 1.0 + 0.12 * math.sin(cycle)
            squash_x = 1.0 - 0.08 * math.sin(cycle)
            arm_l_u_rot = -95.0 + math.sin(cycle * 2) * 20.0
            arm_r_u_rot = -95.0 - math.sin(cycle * 2) * 20.0
            scarf_flutter = math.sin(cycle * 2) * 18.0
            head_tilt = math.sin(cycle) * 10.0
            eye_state = "happy"
            brow_state = "happy"
            mouth_state = "wide_ee"

        elif action == "wave":
            # Warm friendly bear wave
            arm_l_u_rot = -115.0
            arm_l_l_rot = -25.0 + math.sin(t * 7.5) * 30.0
            head_tilt = math.sin(t * 3.0) * 5.0
            scarf_flutter = math.sin(t * 3.0) * 6.0
            y_offset = math.sin(t * 2.5) * 4.0
            eye_state = "happy"
            mouth_state = "smile"

        else:  # Idle
            breathe = math.sin(t * 2.2)
            y_offset = breathe * 3.0
            squash_y = 1.0 + breathe * 0.02
            scarf_flutter = math.sin(t * 2.0) * 4.0

        if eye_state is None:
            blink_c = (t + 1.2) % 3.5
            eye_state = "blink" if 3.2 <= blink_c <= 3.38 else "open"

        if is_speaking and mouth_state is None:
            v_idx = int(t * 8.0) % 4
            mouth_state = ["open_ah", "wide_ee", "round_oh", "smile"][v_idx]
        elif mouth_state is None:
            mouth_state = "smile"

        # ---------------------------------------------------------------------
        # SKELETAL COMPOSITING (Golu Hierarchy)
        # ---------------------------------------------------------------------
        center_x = canvas_w // 2
        hip_y = int(340 + y_offset)

        # 1. Back (Right) Leg
        leg_r = self._render_limb(self.g_leg_u, self.g_leg_l, leg_r_u_rot, leg_r_l_rot, joint_offset=(22, 22))
        canvas.alpha_composite(leg_r, (center_x - 70, hip_y + 35))

        # 2. Back (Right) Arm
        arm_r = self._render_limb(self.g_arm_u, self.g_arm_l, arm_r_u_rot, arm_r_l_rot, joint_offset=(22, 22))
        canvas.alpha_composite(arm_r, (center_x - 105, hip_y - 90))

        # 3. Chubby Torso
        torso_w = int(self.g_torso.width * squash_x)
        torso_h = int(self.g_torso.height * squash_y)
        torso_sc = self.g_torso.resize((torso_w, torso_h), Image.Resampling.LANCZOS)
        canvas.alpha_composite(torso_sc, (center_x - torso_w // 2, hip_y - 85))

        # 4. Front (Left) Leg
        leg_l = self._render_limb(self.g_leg_u, self.g_leg_l, leg_l_u_rot, leg_l_l_rot, joint_offset=(22, 22))
        canvas.alpha_composite(leg_l, (center_x - 10, hip_y + 40))

        # 5. Head (with facial features)
        head_cx = center_x
        head_cy = hip_y - 125
        head_im = self.g_head.copy()
        # Eyes
        ey = self.g_eyes.get(eye_state, self.g_eyes["open"])
        head_im.alpha_composite(ey, (105, 120))
        head_im.alpha_composite(ey, (195, 120))
        # Eyebrows
        br = self.g_brows.get(brow_state, self.g_brows["neutral"])
        head_im.alpha_composite(br, (105, 90))
        head_im.alpha_composite(br, (195, 90))
        # Mouth
        mo = self.g_mouths.get(mouth_state, self.g_mouths["smile"])
        head_im.alpha_composite(mo, (145, 210))

        head_rot = head_im.rotate(head_tilt, resample=Image.Resampling.BICUBIC, center=(180, 220))
        canvas.alpha_composite(head_rot, (head_cx - 180, head_cy - 120))

        # 6. Yellow Scarf (wrapped around neck with flutter)
        scarf_rot = self.g_scarf.rotate(scarf_flutter, resample=Image.Resampling.BICUBIC, center=(140, 40))
        canvas.alpha_composite(scarf_rot, (head_cx - 140, head_cy + 45))

        # 7. Front (Left) Arm
        arm_l = self._render_limb(self.g_arm_u, self.g_arm_l, arm_l_u_rot, arm_l_l_rot, joint_offset=(22, 22))
        canvas.alpha_composite(arm_l, (center_x + 35, hip_y - 90))

        # 8. Held Prop
        if held_item and held_item in self.props:
            prop = self.props[held_item]
            prop_sc = prop.resize((95, 110), Image.Resampling.LANCZOS)
            px = center_x + (90 if action == "receive" else 35)
            py = hip_y - (95 if action == "munch" else 35)
            canvas.alpha_composite(prop_sc, (px, py))

        if facing < 0:
            canvas = canvas.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if scale != 1.0:
            nw = int(canvas_w * scale)
            nh = int(canvas_h * scale)
            canvas = canvas.resize((nw, nh), Image.Resampling.LANCZOS)

        return canvas

    # =========================================================================
    # KINEMATIC HELPER: ROTATING 2-BONE LIMBS (Shoulder->Elbow->Hand)
    # =========================================================================
    def _render_limb(self, upper_img, lower_img, upper_rot, lower_rot, joint_offset=(20, 20)):
        """Renders 2-bone articulated limb with natural joint overlap."""
        w = max(upper_img.width, lower_img.width) + 80
        h = upper_img.height + lower_img.height + 60
        limb_canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        # Upper limb rotated from shoulder/hip anchor
        u_rot = upper_img.rotate(upper_rot, resample=Image.Resampling.BICUBIC, center=joint_offset)
        limb_canvas.alpha_composite(u_rot, (20, 20))

        # Lower limb connected at elbow/knee joint
        # Compute forward kinematics offset for joint
        rad = math.radians(upper_rot)
        bone_len = upper_img.height * 0.65
        jx = int(20 + joint_offset[0] + math.sin(rad) * bone_len)
        jy = int(20 + joint_offset[1] + math.cos(rad) * bone_len)

        l_rot = lower_img.rotate(upper_rot + lower_rot, resample=Image.Resampling.BICUBIC, center=joint_offset)
        limb_canvas.alpha_composite(l_rot, (jx - joint_offset[0], jy - joint_offset[1]))

        return limb_canvas

    def test_all_poses(self):
        """Verifies that all action poses render cleanly without exception."""
        print("🧪 Testing Chintu poses...")
        for act in ["idle", "hop", "walk", "crouch_and_reach", "hold_up", "give", "munch", "wave"]:
            im = self.render_chintu(1.0, action=act, action_progress=0.5, held_item="apple_whole")
            assert im.size == (480, 560), f"Invalid size for Chintu {act}"

        print("🧪 Testing Golu poses...")
        for act in ["idle", "walk_sad", "receive", "munch", "dance", "wave"]:
            im = self.render_golu(1.0, action=act, action_progress=0.5, held_item="apple_half_golu")
            assert im.size == (500, 580), f"Invalid size for Golu {act}"

        print("✅ All kinematic poses verified successfully!")


if __name__ == "__main__":
    rig = CharacterRigV2()
    rig.test_all_poses()
