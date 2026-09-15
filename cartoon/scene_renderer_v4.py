"""
scene_renderer_v4.py
--------------------
Production-Quality Scene Compositor & Renderer for Cartoon V4:
"Mimi's Magic Toy Train" (मीमी और जादुई रेलगाड़ी).

Key Upgrades:
1. Ground Contact Shadows: Soft blurred radial gradient ellipses beneath feet and props.
2. Dynamic Look-At Gaze Tracking: Active pupil targeting toward interactive objects.
3. Natural Acting Sequences: Deceleration into stops, anticipation crouching, true paw contact.
4. Subtitle Redesign: Compact, unobtrusive subtitles positioned in bottom safe area.
5. Cinematic Camera Moves: Smooth ease-in-out quadratic curves and safe headroom.
6. Non-blocking FFmpeg rawvideo pipe encoding.
"""

import os
import sys
import time
import math
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import (
    CARTOON_DIR,
    OUTPUT_DIR,
    WIDTH,
    HEIGHT,
    FPS,
)
from cartoon.character_rig_v4 import (
    CharacterRigV4,
    ease_in_out_quad,
    ease_out_quad,
    ease_in_quad
)

ASSETS_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3")
BG_DIR = os.path.join(ASSETS_V3_DIR, "backgrounds")
PROPS_DIR = os.path.join(ASSETS_V3_DIR, "props")
AUDIO_V3_DIR = os.path.join(ASSETS_V3_DIR, "audio")


class SceneRendererV4:
    def __init__(self, environment=None, character=None):
        self.rig = CharacterRigV4()
        self.character = character or "mimi"
        self.environment = environment or "playroom"
        self._load_environment()

    def _load_environment(self):
        # Multi-plane background layers (1920x1080)
        env = (self.environment or "playroom").lower()
        if "lab" in env:
            far_p = os.path.join(BG_DIR, "bg_lab_far.png")
            mid_p = os.path.join(BG_DIR, "bg_lab_mid.png")
            fg_p = os.path.join(BG_DIR, "bg_lab_fg.png")
        elif "space" in env:
            far_p = os.path.join(BG_DIR, "bg_space_far.png")
            mid_p = os.path.join(BG_DIR, "bg_space_mid.png")
            fg_p = os.path.join(BG_DIR, "bg_space_fg.png")
        else:
            far_p = os.path.join(BG_DIR, "bg_playroom_far.png")
            mid_p = os.path.join(BG_DIR, "bg_playroom_mid.png")
            fg_p = os.path.join(BG_DIR, "bg_playroom_fg.png")

        if not os.path.exists(far_p):
            far_p = os.path.join(BG_DIR, "bg_playroom_far.png")
            mid_p = os.path.join(BG_DIR, "bg_playroom_mid.png")
            fg_p = os.path.join(BG_DIR, "bg_playroom_fg.png")

        self.bg_far = Image.open(far_p).convert("RGBA")
        self.bg_mid = Image.open(mid_p).convert("RGBA")
        self.bg_fg = Image.open(fg_p).convert("RGBA")

        # Environmental Sprites
        self.spr_steam = Image.open(os.path.join(PROPS_DIR, "steam_cloud.png")).convert("RGBA")
        self.spr_sparkle = Image.open(os.path.join(PROPS_DIR, "sparkle_gold.png")).convert("RGBA")

    def render_frame(self, t, timing_metadata):
        """Renders a single production-quality 1080p frame at timestamp t."""
        # ---------------------------------------------------------------------
        # 1. Active Scene and Dialogue State
        # ---------------------------------------------------------------------
        active_scene = 1
        for i, item in enumerate(timing_metadata):
            next_start = timing_metadata[i + 1]["start_time"] if i + 1 < len(timing_metadata) else 999999.0
            if t < next_start:
                active_scene = item["scene_id"]
                break
        else:
            active_scene = timing_metadata[-1]["scene_id"]

        is_speech = any(item["start_time"] <= t <= (item["end_time"] + 0.15) for item in timing_metadata)

        # Base camera in world space (1920x1080)
        cam_x, cam_y, zoom = 960, 540, 1.0

        # Mimi Transform & State
        m_world_x, m_world_y = 500, 480
        m_scale = 0.54
        m_flip = False
        m_tilt = 0.0
        m_squash = (1.0, 1.0)
        m_eye = "open"
        m_gaze = (0.0, 0.0)
        m_mouth = None
        m_paw_reach = 0.0
        m_jump_height = 0.0

        # Train Transform & State
        t_world_x, t_world_y = 1180, 750
        t_scale = 0.28
        t_flip = False
        t_tilt = 0.0
        t_wheel_rot = 0.0
        t_lifted = 0.0
        show_train = True
        steam_puffs = []
        sparkles = []

        # Ground plane reference
        floor_y = 905
        train_floor_y = 880

        # ---------------------------------------------------------------------
        # 2. Natural Acting & Kinematics Choreography
        # ---------------------------------------------------------------------
        if active_scene == 1:
            # SCENE 1 (0.00 - 6.36s): Playroom Hook & Trotting Entrance
            s_dur = 6.36
            s_prog = min(1.0, max(0.0, t / s_dur))

            # Camera: Smooth cinematic push-in tracking Mimi
            e_cam = ease_in_out_quad(s_prog)
            zoom = 1.0 + e_cam * 0.10
            cam_x = int(820 + e_cam * 160)
            cam_y = 540

            # Mimi trots in from left and decelerates as she spots the train
            walk_prog = ease_out_quad(min(1.0, s_prog * 1.15))
            m_world_x = int(160 + walk_prog * 540)

            # Trotting bounce with natural deceleration
            step_rate = 8.5 * (1.0 - 0.35 * s_prog)
            bounce = abs(math.sin(t * step_rate)) * 16.0 * (1.0 - 0.5 * s_prog)
            m_world_y = int(495 - bounce)
            m_jump_height = bounce
            m_tilt = math.sin(t * step_rate) * 2.2 * (1.0 - 0.5 * s_prog)
            m_squash = (1.0 + math.sin(t * step_rate) * 0.03, 1.0 - math.sin(t * step_rate) * 0.03)

            # Gaze: Looking around, then locking onto train on right at t > 3.8s
            if s_prog < 0.60:
                m_gaze = (math.sin(t * 2.0) * 4.0, math.cos(t * 1.5) * 3.0)
                m_eye = "happy" if (t % 2.5 < 1.2) else "open"
            else:
                # Spots the train! Look down-right
                look_p = ease_out_quad((s_prog - 0.60) / 0.40)
                m_gaze = (8.0 * look_p, 9.0 * look_p)
                m_eye = "wide" if (s_prog < 0.85) else "open"
                m_tilt = 3.0 * look_p

            # Train sits idle on floor near blocks
            t_world_x, t_world_y = 1180, 750
            t_scale = 0.28

        elif active_scene == 2:
            # SCENE 2 (6.61 - 13.55s): Discovery, Kneeling & Lifting with Weight
            s_start, s_dur = 6.61, 6.94
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Medium close-up on discovery and pickup
            e_cam = ease_in_out_quad(s_prog)
            zoom = 1.18 + e_cam * 0.08
            cam_x = 1040
            cam_y = 560

            if s_prog < 0.22:
                # Phase 1: Final approach steps and deceleration to stop
                p = s_prog / 0.22
                ep = ease_out_quad(p)
                m_world_x = int(700 + ep * 240)
                bounce = abs(math.sin(t * 7.5)) * 12.0 * (1.0 - p)
                m_world_y = int(495 - bounce)
                m_jump_height = bounce
                m_gaze = (9.0, 10.0)  # Looking down at train
                m_eye = "open"
                t_world_x, t_world_y = 1180, 750
            elif s_prog < 0.48:
                # Phase 2: Crouch anticipation and paw reach toward train
                p = (s_prog - 0.22) / 0.26
                ep = ease_in_out_quad(p)
                m_world_x = 940
                # Knees bend down
                crouch = ep * 32.0
                m_world_y = int(495 + crouch)
                m_squash = (1.0 + ep * 0.07, 1.0 - ep * 0.07)
                m_tilt = 4.5 * ep
                m_gaze = (6.0 + ep * 3.0, 12.0)  # Eyes focused on contact point
                m_eye = "open"
                m_paw_reach = ep  # Paw extends down to train handle

                # Train remains grounded
                t_world_x = 1170
                t_world_y = 750
                t_scale = 0.28
            elif s_prog < 0.72:
                # Phase 3: Paw contacts train and lifts upward with weight
                p = (s_prog - 0.48) / 0.24
                ep = ease_out_quad(p)
                m_world_x = 940
                # Body rises back up
                m_world_y = int(527 - ep * 37)
                m_squash = (1.0 + (1.0 - ep) * 0.05, 1.0 - (1.0 - ep) * 0.05)
                m_tilt = 4.5 * (1.0 - ep)
                m_gaze = (5.0, 8.0)  # Eyes follow train rising
                m_eye = "wide" if (p > 0.4) else "open"
                m_paw_reach = 1.0 - ep * 0.5

                # Train lifts into paws
                t_lifted = ep
                t_world_x = int(1170 - ep * 110)
                t_world_y = int(750 - ep * 125)
                t_tilt = -3.0 * math.sin(p * math.pi)
                t_scale = 0.26 + 0.02 * (1.0 - ep)
            else:
                # Phase 4: Holding train happily in front of chest, admiring bell
                p = (s_prog - 0.72) / 0.28
                m_world_x = 940
                breath = math.sin(t * 3.5) * 5.0
                m_world_y = int(490 - breath)
                m_squash = (1.0, 1.0)
                m_eye = "happy" if (int(t * 2.5) % 2 == 0) else "wide"
                m_gaze = (4.0, 7.0)  # Admiring train
                t_lifted = 1.0
                t_world_x = 1060
                t_world_y = int(625 - breath)
                t_scale = 0.26

        elif active_scene == 3:
            # SCENE 3 (13.80 - 19.65s): Stepping to Track & Precise Rail Placement
            s_start, s_dur = 13.80, 5.85
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Smooth tracking pan
            e_cam = ease_in_out_quad(s_prog)
            zoom = 1.20
            cam_x = int(1040 + e_cam * 60)
            cam_y = 565

            if s_prog < 0.42:
                # Phase 1: Carrying train to track
                p = s_prog / 0.42
                ep = ease_in_out_quad(p)
                m_world_x = int(940 + ep * 120)
                bounce = abs(math.sin(t * 7.5)) * 10.0
                m_world_y = int(490 - bounce)
                m_jump_height = bounce
                m_gaze = (6.0, 9.0)  # Looking at track spot ahead
                m_eye = "open"
                t_lifted = 1.0
                t_world_x = m_world_x + 95
                t_world_y = m_world_y + 115 - int(bounce * 0.5)
                t_scale = 0.26
            elif s_prog < 0.74:
                # Phase 2: Kneeling down and placing train accurately on rails
                p = (s_prog - 0.42) / 0.32
                ep = ease_in_out_quad(p)
                m_world_x = 1060
                # Knees bend down
                bend = ep * 28.0
                m_world_y = int(490 + bend)
                m_squash = (1.0 + ep * 0.06, 1.0 - ep * 0.06)
                m_tilt = 4.0 * ep
                m_gaze = (5.0, 11.0)  # Watching rail alignment
                m_eye = "open"
                m_paw_reach = ep

                # Train lowers onto track
                t_lifted = 1.0 - ep
                t_world_x = int(1155 + ep * 15)
                t_world_y = int(625 + ep * 125)
                t_scale = 0.26 + ep * 0.02
            else:
                # Phase 3: Mimi stands back up with pleased smile; train settles on rails
                p = (s_prog - 0.74) / 0.26
                ep = ease_out_quad(p)
                m_world_x = 1060
                m_world_y = int(518 - ep * 28)
                m_squash = (1.0, 1.0)
                m_tilt = 0.0
                m_gaze = (0.0, 0.0)
                m_eye = "happy"
                m_mouth = "smile"
                m_paw_reach = 0.0

                t_lifted = 0.0
                t_world_x = 1170
                # Tiny physical settle bounce when hitting rails
                settle = math.sin(p * math.pi * 2.0) * math.exp(-p * 5.0) * 3.0
                t_world_y = int(750 + settle)
                t_scale = 0.28

        elif active_scene == 4:
            # SCENE 4 (19.90 - 27.51s): Magic Sparkle Burst, Whistle & Joyful Clapping!
            s_start, s_dur = 19.90, 7.61
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Framing both Mimi and the smoking train
            zoom = 1.22
            cam_x = 1060
            cam_y = 560

            # Train awakens: subtle engine vibration, wheel acceleration
            accel_p = ease_in_quad(min(1.0, s_prog * 1.4))
            t_world_x = 1170
            t_vibe = math.sin(t * 30.0) * 1.5 if s_prog < 0.6 else 0.0
            t_world_y = int(750 + t_vibe)
            t_scale = 0.28
            t_wheel_rot = (t - s_start) * 580.0 * accel_p

            # Steam clouds puff from chimney
            chimney_x = t_world_x + int(190 * t_scale)
            chimney_y = t_world_y + int(45 * t_scale)
            puff_rate = 0.36
            for puff_i in range(9):
                puff_t = s_start + puff_i * puff_rate + 0.5
                if puff_t <= t:
                    age = t - puff_t
                    if age < 1.4:
                        px = chimney_x - int(age * 40)
                        py = chimney_y - int(age * 70)
                        psz = int(32 + age * 68)
                        palpha = max(0.0, 1.0 - (age / 1.4))
                        steam_puffs.append((px, py, psz, palpha))

            # Golden magic sparkles around train
            if 0.12 <= s_prog <= 0.88:
                for sp_i, (ox, oy, spd) in enumerate([(55, -45, 6.5), (125, 15, -7.0), (25, 35, 8.0), (145, -25, -5.5)]):
                    sp_x = t_world_x + ox
                    sp_y = t_world_y + oy
                    sp_sz = int(55 + math.sin(t * spd + sp_i) * 20)
                    sparkles.append((sp_x, sp_y, sp_sz, t * spd * 20.0))

            # Mimi's Acting: Gasp of joy → jump & rhythmic clapping!
            if s_prog < 0.18:
                # Anticipation gasp
                m_world_x = 930
                m_world_y = 495
                m_squash = (1.05, 0.95)
                m_gaze = (8.0, 5.0)  # Eyes wide looking at train
                m_eye = "wide"
            else:
                # Joyful hopping & clapping
                clap_bounce = abs(math.sin((t - s_start) * 9.5)) * 26.0
                m_world_x = 930
                m_world_y = int(495 - clap_bounce)
                m_jump_height = clap_bounce
                m_squash = (1.0 - clap_bounce * 0.004, 1.0 + clap_bounce * 0.004)
                m_gaze = (6.0, 4.0)  # Watching train while cheering
                m_eye = "happy" if (int(t * 4.5) % 2 == 0) else "wide"

        elif active_scene == 5:
            # SCENE 5 (27.76 - 32.85s): Train Chugging Around Track & Cheerful Chase
            s_start, s_dur = 27.76, 5.09
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Wide dynamic playroom tracking
            zoom = 1.14
            cam_x = 1000
            cam_y = 555

            # Train moves along elliptical track loop: center (1080, 750), Rx=260, Ry=75
            track_cx, track_cy = 1080, 750
            rx, ry = 250, 70
            omega = 1.35
            ang = (t - s_start) * omega
            t_world_x = int(track_cx + rx * math.cos(ang))
            t_world_y = int(track_cy + ry * math.sin(ang))
            t_wheel_rot = (t - s_start) * 720.0
            t_flip = math.sin(ang) < 0.0
            # Slight chassis rocking along track
            t_tilt = math.sin(ang * 4.0) * 1.8

            # Steam puff trail
            chim_ox = 60 if not t_flip else -60
            chimney_x = t_world_x + chim_ox
            chimney_y = t_world_y - 20
            for puff_i in range(12):
                puff_t = s_start + puff_i * 0.32
                if puff_t <= t:
                    age = t - puff_t
                    if age < 1.3:
                        px = chimney_x - int(age * 55 * (-1 if t_flip else 1))
                        py = chimney_y - int(age * 60)
                        psz = int(30 + age * 62)
                        palpha = max(0.0, 1.0 - (age / 1.3))
                        steam_puffs.append((px, py, psz, palpha))

            # Mimi playfully trots along outer circuit, eyes tracking the train
            m_ang = ang - 0.45
            m_world_x = int(track_cx - 80 + (rx + 90) * math.cos(m_ang))
            bounce = abs(math.sin(t * 8.5)) * 18.0
            m_world_y = int(track_cy - 220 + ry * math.sin(m_ang) - bounce)
            m_jump_height = bounce
            m_tilt = math.sin(t * 8.5) * 3.0
            m_flip = math.sin(m_ang) < 0.0

            # Dynamic gaze: Pupils track the train!
            gaze_dx = (t_world_x - m_world_x) * 0.03
            gaze_dy = (t_world_y - m_world_y) * 0.03
            m_gaze = (gaze_dx, gaze_dy)
            m_eye = "happy"

        elif active_scene == 6:
            # SCENE 6 (33.10 - 39.96s): Educational Moral Lesson & Warm Goodbye Wave
            s_start, s_dur = 33.10, 6.86
            s_prog = min(1.0, max(0.0, (t - s_start) / s_dur))

            # Camera: Gentle settling pull-back to wide warm framing
            e_cam = ease_in_out_quad(s_prog)
            zoom = 1.20 - e_cam * 0.14
            cam_x = 1000
            cam_y = 540

            # Train resting at front track station, gentle idle steam
            t_world_x, t_world_y = 1200, 750
            t_scale = 0.28
            t_wheel_rot = 0.0

            if int(t * 1.5) % 2 == 0:
                steam_puffs.append((t_world_x + 60, t_world_y - 30, 48, 0.6))

            # Mimi stands proudly in center, gentle breathing & sincere camera eye contact
            m_world_x = 920
            sway = math.sin((t - s_start) * 4.0) * 7.0
            m_world_y = int(480 - abs(math.sin((t - s_start) * 4.0)) * 5.0)
            m_tilt = math.sin((t - s_start) * 4.0) * 3.0
            # Direct camera eye contact for lesson
            m_gaze = (0.0, -1.5)
            m_eye = "happy" if (t % 3.0 < 2.0) else "open"

            # Outro golden sparkles
            if s_prog > 0.35:
                for sp_i, (ox, oy, spd) in enumerate([(-180, -60, 4.0), (220, -40, -4.5), (0, -120, 5.0), (140, 80, -5.5)]):
                    sp_x = m_world_x + ox
                    sp_y = m_world_y + oy
                    sp_sz = int(60 + math.sin(t * spd + sp_i) * 18)
                    sparkles.append((sp_x, sp_y, sp_sz, t * spd * 18.0))

        # ---------------------------------------------------------------------
        # 3. Multi-Plane Parallax Compositing with Contact Shadows
        # ---------------------------------------------------------------------
        frame = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

        crop_w = int(WIDTH / zoom)
        crop_h = int(HEIGHT / zoom)

        # Layer 1: Far Background (Parallax 0.35)
        far_cam_x = int(cam_x * 0.35 + (960 * 0.65))
        far_cam_y = int(cam_y * 0.35 + (540 * 0.65))
        far_cx = max(0, min(1920 - crop_w, far_cam_x - crop_w // 2))
        far_cy = max(0, min(1080 - crop_h, far_cam_y - crop_h // 2))
        far_crop = self.bg_far.crop((far_cx, far_cy, far_cx + crop_w, far_cy + crop_h))
        far_scaled = far_crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        frame.alpha_composite(far_scaled, (0, 0))

        # Layer 2: Midground (Hardwood Floor, Green Rug, Tracks - Parallax 1.0)
        mid_cx = max(0, min(1920 - crop_w, cam_x - crop_w // 2))
        mid_cy = max(0, min(1080 - crop_h, cam_y - crop_h // 2))
        mid_crop = self.bg_mid.crop((mid_cx, mid_cy, mid_cx + crop_w, mid_cy + crop_h))
        mid_scaled = mid_crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        frame.alpha_composite(mid_scaled, (0, 0))

        # ---------------------------------------------------------------------
        # Ground Contact Shadows (Rendered on top of floor before characters)
        # ---------------------------------------------------------------------
        # Train Contact Shadow (Grounded on rails; fades out when lifted into paws)
        if show_train and t_lifted < 0.95:
            tr_shadow_op = int(160 * (1.0 - t_lifted))
            tr_shadow_w = int(260 * t_scale * 3.4 * zoom)
            tr_shadow_h = int(65 * t_scale * 3.4 * zoom)
            if tr_shadow_w > 8 and tr_shadow_h > 4:
                sh_train = self.rig.render_contact_shadow(tr_shadow_w, tr_shadow_h, blur_radius=9, opacity=tr_shadow_op)
                train_base_y = t_world_y + int(816 * t_scale)
                sh_tx = int((t_world_x + int(968 * t_scale * 0.5) - mid_cx) * zoom) - sh_train.width // 2
                sh_ty = int((train_base_y - 8 - mid_cy) * zoom) - sh_train.height // 2
                frame.alpha_composite(sh_train, (sh_tx, sh_ty))

        # Mimi Contact Shadow (Grounded at foot line; softens and spreads when hopping)
        m_shadow_atten = max(0.35, 1.0 - m_jump_height / 140.0)
        m_shadow_op = int(165 * m_shadow_atten)
        m_shadow_w = int(220 * m_scale * zoom * (1.0 + m_jump_height * 0.006))
        m_shadow_h = int(58 * m_scale * zoom * (1.0 + m_jump_height * 0.006))
        if m_shadow_w > 8 and m_shadow_h > 4:
            sh_mimi = self.rig.render_contact_shadow(m_shadow_w, m_shadow_h, blur_radius=10, opacity=m_shadow_op)
            mimi_foot_y = (m_world_y + m_jump_height) + int(807 * m_scale)
            sh_mx = int((m_world_x + int(530 * m_scale * 0.5) - mid_cx) * zoom) - sh_mimi.width // 2
            sh_my = int((mimi_foot_y - 10 - mid_cy) * zoom) - sh_mimi.height // 2
            frame.alpha_composite(sh_mimi, (sh_mx, sh_my))

        # ---------------------------------------------------------------------
        # Layer 3: Character & Prop Action Plane (Parallax 1.0)
        # ---------------------------------------------------------------------
        # 3A. Train
        if show_train:
            im_train = self.rig.render_toy_train(
                wheel_rot_deg=t_wheel_rot, scale=t_scale, flip_h=t_flip, body_tilt=t_tilt
            )
            tx_scr = int((t_world_x - mid_cx) * zoom)
            ty_scr = int((t_world_y - mid_cy) * zoom)
            frame.alpha_composite(im_train, (tx_scr, ty_scr))

        # 3B. Steam Puffs
        for px, py, psz, palpha in steam_puffs:
            sx_scr = int((px - mid_cx) * zoom)
            sy_scr = int((py - mid_cy) * zoom)
            sc_sz = int(psz * zoom)
            if sc_sz > 4 and 0 <= sx_scr < WIDTH and 0 <= sy_scr < HEIGHT:
                sp_img = self.spr_steam.resize((sc_sz, sc_sz), Image.Resampling.BILINEAR)
                if palpha < 0.98:
                    arr_sp = np.array(sp_img)
                    arr_sp[:, :, 3] = (arr_sp[:, :, 3] * palpha).astype(np.uint8)
                    sp_img = Image.fromarray(arr_sp, "RGBA")
                frame.alpha_composite(sp_img, (sx_scr, sy_scr))

        # 3C. Golden Sparkles
        for sp_x, sp_y, sp_sz, sp_rot_deg in sparkles:
            spx_scr = int((sp_x - mid_cx) * zoom)
            spy_scr = int((sp_y - mid_cy) * zoom)
            cur_sz = int(sp_sz * zoom)
            if cur_sz > 4 and 0 <= spx_scr < WIDTH and 0 <= spy_scr < HEIGHT:
                sp_rot = self.spr_sparkle.rotate(sp_rot_deg, resample=Image.Resampling.BILINEAR)
                sp_img = sp_rot.resize((cur_sz, cur_sz), Image.Resampling.BILINEAR)
                frame.alpha_composite(sp_img, (spx_scr - cur_sz // 2, spy_scr - cur_sz // 2))

        # 3D. Mimi the Kitten
        im_mimi = self.rig.render_character(self.character, 
            t,
            acting_state="acting",
            is_speaking=is_speech,
            eye_state=m_eye,
            gaze_offset=m_gaze,
            mouth_state=m_mouth,
            squash_stretch=m_squash,
            tilt_deg=m_tilt,
            flip_h=m_flip,
            paw_reach=m_paw_reach,
        )
        mw = int(im_mimi.width * m_scale * zoom)
        mh = int(im_mimi.height * m_scale * zoom)
        im_mimi_sc = im_mimi.resize((mw, mh), Image.Resampling.BILINEAR)
        mx_scr = int((m_world_x - mid_cx) * zoom)
        my_scr = int((m_world_y - mid_cy) * zoom)
        frame.alpha_composite(im_mimi_sc, (mx_scr, my_scr))

        # Layer 4: Foreground Framing Layer (Potted Plant Leaves - Parallax 1.35)
        fg_cam_x = int(cam_x * 1.35 - (960 * 0.35))
        fg_cam_y = int(cam_y * 1.35 - (540 * 0.35))
        fg_cx = max(0, min(1920 - crop_w, fg_cam_x - crop_w // 2))
        fg_cy = max(0, min(1080 - crop_h, fg_cam_y - crop_h // 2))
        fg_crop = self.bg_fg.crop((fg_cx, fg_cy, fg_cx + crop_w, fg_cy + crop_h))
        fg_scaled = fg_crop.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
        frame.alpha_composite(fg_scaled, (0, 0))

        return frame.convert("RGB")

    def render_animation_video(self, timing_metadata, audio_path, srt_path, output_video_path):
        """
        Pipes raw RGB24 video frames into FFmpeg with stderr redirected to log.
        Uses redesigned compact subtitles (Fontsize=17, MarginV=20) positioned
        strictly in the bottom safe area so they never obstruct characters.
        """
        total_duration = timing_metadata[-1]["end_time"] + 0.4
        total_frames = int(total_duration * FPS)

        print(f"🎬 [V4] Rendering {total_frames} frames ({total_duration:.2f}s) at {FPS} FPS...", flush=True)

        clean_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        # Redesigned Subtitle Filter: Smaller font (17pt), safe bottom margin (20px), crisp black outline
        sub_filter = (
            f"subtitles='{clean_srt}':force_style="
            f"'Fontname=Arial,Fontsize=17,PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00181010,Outline=2.0,Shadow=1.0,MarginV=20,Alignment=2'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-nostats",
            "-loglevel", "warning",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-pix_fmt", "rgb24",
            "-r", str(FPS),
            "-i", "pipe:0",
            "-i", audio_path,
            "-vf", sub_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_video_path
        ]

        ffmpeg_log = os.path.join(OUTPUT_DIR, "ffmpeg_render_v4.log")
        with open(ffmpeg_log, "w", encoding="utf-8") as f_err:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=f_err)

            t_start = time.time()

            for i in range(total_frames):
                t = i / float(FPS)
                frame_rgb = self.render_frame(t, timing_metadata)
                raw_bytes = frame_rgb.tobytes()
                proc.stdin.write(raw_bytes)
                if i > 0 and i % 150 == 0:
                    cur_fps = i / (time.time() - t_start + 0.001)
                    pct = (i / total_frames) * 100
                    print(f"  Frame {i}/{total_frames} ({pct:.1f}%) | Speed: {cur_fps:.1f} fps", flush=True)

            proc.stdin.close()
            proc.wait()

        if proc.returncode != 0:
            err_msg = ""
            if os.path.exists(ffmpeg_log):
                with open(ffmpeg_log, "r", encoding="utf-8", errors="replace") as f_err:
                    err_msg = f_err.read()
            raise RuntimeError(f"FFmpeg encoding failed (exit {proc.returncode}):\\n{err_msg[-600:]}")

        elapsed = time.time() - t_start
        file_size = os.path.getsize(output_video_path)
        print(f"✅ Cartoon Video V4 successfully rendered: {output_video_path}", flush=True)
        print(f"   Size: {file_size:,} bytes | Elapsed: {elapsed:.2f}s ({total_frames / elapsed:.1f} fps)", flush=True)
        return output_video_path


def test_frame_v4():
    print("Testing SceneRendererV4 frame generation...", flush=True)
    timing_file = os.path.join(AUDIO_V3_DIR, "timing_metadata.json")
    with open(timing_file, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    renderer = SceneRendererV4()
    test_times = [2.5, 9.5, 16.5, 23.5, 30.0, 37.0]
    for s_idx, t in enumerate(test_times, 1):
        f = renderer.render_frame(t, timing_meta)
        out_p = os.path.join(OUTPUT_DIR, f"preview_v4_scene{s_idx}.jpg")
        f.save(out_p, quality=92)
        print(f"  Scene {s_idx} preview frame saved: {out_p}", flush=True)

    print("✅ All 6 scene preview frames rendered successfully with contact shadows & gaze tracking!", flush=True)


if __name__ == "__main__":
    test_frame_v4()
