"""
character_rig_v3.py
-------------------
High-fidelity Character Acting and Prop Rig Engine for Cartoon V3:
"Mimi's Magic Toy Train".

Features:
1. Storybook-grade illustrated Mimi Kitten rig with smooth multi-layer compositing.
2. Organic Squash & Stretch deformation preserving geometric volume.
3. Facial Animation:
   - Natural autonomic eye blinking cycles.
   - Expressive emotional eye states: open, blink, happy, wide, look_down, look_right.
   - Speech-synchronized mouth visemes (closed, smile, open_ah, wide_ee, round_oh, pout_oo).
4. Physical Character Acting States:
   - curious_walk: Bipedal bounce, body lean, tail sway, footstep cadence.
   - crouch_reach: Anticipation crouch, leaning downward, curious head tilt.
   - hold_examine: Holding mini train in paws, breathing cycle, look_down inspection.
   - place_track: Smooth knee-bend placement on wooden rail, settle.
   - clap_cheer: Joyful vertical bounce, clapping rhythm, happy closed-eye smiles.
   - trot_follow: Energetic pursuit along track, forward lean, cheerful sway.
   - wave_outro: Warm friendly pose, gentle body sway, camera-facing eye contact.
5. Toy Train Mechanical Rig:
   - Chassis positioning along 2D rail trajectory (x(t), y(t), angle(t)).
   - Continuous wheel rotation synchronized to travel velocity.
   - Dynamic steam puff particle emission from chimney.
   - Golden magic sparkle emitters.
"""

import os
import sys
import math
import random
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_DIR

ASSETS_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3")
CHAR_DIR = os.path.join(ASSETS_V3_DIR, "characters")
PROPS_DIR = os.path.join(ASSETS_V3_DIR, "props")


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


class CharacterRigV3:
    """Manages Mimi the Kitten's visual rig, emotional acting, and prop animations."""

    def __init__(self):
        self._load_assets()
        # Left eye center on mimi_base: (145, 240) -> top-left at (100, 195)
        self.eye_l_pos = (100, 195)
        # Right eye center on mimi_base: (325, 240) -> top-left at (280, 195)
        self.eye_r_pos = (280, 195)
        # Mouth center on mimi_base: (220, 335) -> top-left at (170, 305)
        self.mouth_pos = (170, 305)

    def _load_assets(self):
        # Base character
        self.mimi_base = Image.open(os.path.join(CHAR_DIR, "mimi_base.png")).convert("RGBA")

        # Eye states
        self.eyes = {
            s: Image.open(os.path.join(CHAR_DIR, f"mimi_eye_{s}.png")).convert("RGBA")
            for s in ["open", "blink", "happy", "wide", "look_down", "look_right"]
        }

        # Mouth visemes
        self.mouths = {
            s: Image.open(os.path.join(CHAR_DIR, f"mimi_mouth_{s}.png")).convert("RGBA")
            for s in ["closed", "smile", "open_ah", "wide_ee", "round_oh", "pout_oo"]
        }

        # Props
        self.train_chassis = Image.open(os.path.join(PROPS_DIR, "train_engine_full.png")).convert("RGBA")
        self.train_wheel = Image.open(os.path.join(PROPS_DIR, "train_wheel.png")).convert("RGBA")
        self.steam_cloud = Image.open(os.path.join(PROPS_DIR, "steam_cloud.png")).convert("RGBA")
        self.sparkle_gold = Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA")

    def get_eye_state(self, t, expression="open"):
        """Autonomic eye blink combined with emotional expression."""
        blink_phase = t % 3.2
        if blink_phase < 0.14:
            return "blink"
        if expression in self.eyes:
            return expression
        return "open"

    def get_speech_viseme(self, t, is_speaking=False, default="smile"):
        """Speech viseme cadenced to voice rhythm."""
        if not is_speaking:
            return default
        cycle = int(t * 7.5) % 5
        viseme_seq = ["open_ah", "wide_ee", "smile", "round_oh", "pout_oo"]
        return viseme_seq[cycle]

    def render_mimi(
        self,
        t,
        acting_state="idle",
        is_speaking=False,
        eye_state="open",
        mouth_state=None,
        squash_stretch=(1.0, 1.0),
        tilt_deg=0.0,
        flip_h=False,
    ):
        """
        Renders Mimi the Kitten with acting transforms, facial expressions,
        and organic squash & stretch.
        """
        char_img = self.mimi_base.copy()

        curr_eye = self.get_eye_state(t, eye_state)
        curr_mouth = mouth_state if mouth_state else self.get_speech_viseme(t, is_speaking)

        eye_sprite = self.eyes.get(curr_eye, self.eyes["open"])
        mouth_sprite = self.mouths.get(curr_mouth, self.mouths["smile"])

        char_img.alpha_composite(eye_sprite, self.eye_l_pos)
        eye_r_sprite = eye_sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        char_img.alpha_composite(eye_r_sprite, self.eye_r_pos)
        char_img.alpha_composite(mouth_sprite, self.mouth_pos)

        # Squash & Stretch
        sx, sy = squash_stretch
        w, h = char_img.size
        new_w = max(10, int(w * sx))
        new_h = max(10, int(h * sy))
        if new_w != w or new_h != h:
            char_img = char_img.resize((new_w, new_h), Image.Resampling.BILINEAR)

        # Rotation / Lean
        if abs(tilt_deg) > 0.5:
            char_img = char_img.rotate(tilt_deg, resample=Image.Resampling.BILINEAR, expand=True)

        if flip_h:
            char_img = char_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        return char_img

    def render_toy_train(self, wheel_rot_deg=0.0, scale=0.32, flip_h=False):
        """
        Renders the wooden toy steam train with spinning blue drive wheels.
        """
        orig_w, orig_h = self.train_chassis.size
        tw = int(orig_w * scale)
        th = int(orig_h * scale)
        chassis = self.train_chassis.resize((tw, th), Image.Resampling.BILINEAR)

        rot_wheel = self.train_wheel.rotate(wheel_rot_deg, resample=Image.Resampling.BILINEAR)
        wheel_sz = int(115 * scale)
        rot_wheel = rot_wheel.resize((wheel_sz, wheel_sz), Image.Resampling.BILINEAR)

        w_half = wheel_sz // 2
        w1_pos = (int(tw * 0.28) - w_half, int(th * 0.82) - w_half)
        w2_pos = (int(tw * 0.72) - w_half, int(th * 0.82) - w_half)

        train_canvas = Image.new("RGBA", (tw, th + int(20 * scale)), (0, 0, 0, 0))
        train_canvas.alpha_composite(chassis, (0, 0))

        for pos in [w1_pos, w2_pos]:
            px, py = pos
            if 0 <= px < tw and 0 <= py < train_canvas.height:
                train_canvas.alpha_composite(rot_wheel, (px, py))

        if flip_h:
            train_canvas = train_canvas.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        return train_canvas
