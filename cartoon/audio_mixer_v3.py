"""
audio_mixer_v3.py
-----------------
Master multi-track audio designer for Cartoon Version 3: "Mimi's Magic Toy Train".
Integrates:
1. Crystal-clear Hindi Edge-TTS narration.
2. Ducked cheerful toybox musical soundtrack (-18.4 dB during speech).
3. Synchronized cartoon sound effects:
   - Soft kitten footstep patters
   - Train pickup whoosh
   - Wooden track rail placement click
   - Steam train whistle ("Choo-choo!")
   - Rhythmic steam engine chugging ("chug-chug-chug")
   - Joyful paw clapping
   - Magical starburst sparkle chime
Produces: C:\\kids_automation\\cartoon\\assets_v3\\audio\\final_master_audio_v3.wav
"""

import os
import sys
import math
import json
import numpy as np
import scipy.io.wavfile as wavfile

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_DIR, MUSIC_VOLUME, SFX_VOLUME

AUDIO_V3_DIR = os.path.join(CARTOON_DIR, "assets_v3", "audio")


def synthesize_toy_sfx():
    """Synthesizes high-quality cartoon SFX for toy train and kitten actions."""
    sr = 48000

    # 1. Train Whistle "Choo-Choo!" (0.85s dual tone)
    t = np.linspace(0, 0.85, int(sr * 0.85), endpoint=False)
    # Whistle chord: 587 Hz (D5) + 880 Hz (A5) with vibrato
    vib = np.sin(2 * np.pi * 6.0 * t) * 12.0
    w1 = np.sin(2 * np.pi * (587.0 + vib) * t)
    w2 = np.sin(2 * np.pi * (880.0 + vib) * t) * 0.7
    w3 = np.sin(2 * np.pi * (1174.0 + vib) * t) * 0.35
    # Two blast envelope: "choo ... chooo!"
    s1 = np.maximum(0.0, np.sin(np.pi * np.clip(t / 0.35, 0.0, 1.0)))
    env1 = np.where(t < 0.35, s1 ** 1.5, 0.0)
    s2 = np.maximum(0.0, np.sin(np.pi * np.clip((t - 0.40) / 0.45, 0.0, 1.0)))
    env2 = np.where(t > 0.40, s2 ** 1.5, 0.0)
    whistle = (w1 + w2 + w3) * (env1 * 0.8 + env2 * 1.0) * 0.45
    w_stereo = np.column_stack([whistle, whistle])
    wavfile.write(os.path.join(AUDIO_V3_DIR, "sfx_train_whistle.wav"), sr, (w_stereo * 32767).astype(np.int16))

    # 2. Steam Train Chug (0.18s rhythmic burst)
    t_chug = np.linspace(0, 0.18, int(sr * 0.18), endpoint=False)
    noise = np.random.uniform(-0.8, 0.8, len(t_chug))
    env_chug = np.sin(np.pi * t_chug / 0.18) ** 2.0
    chug = noise * env_chug * 0.35
    c_stereo = np.column_stack([chug, chug])
    wavfile.write(os.path.join(AUDIO_V3_DIR, "sfx_train_chug.wav"), sr, (c_stereo * 32767).astype(np.int16))

    # 3. Wooden Track Click (0.15s crisp wooden snap)
    t_click = np.linspace(0, 0.15, int(sr * 0.15), endpoint=False)
    tone = np.sin(2 * np.pi * 680 * t_click) * np.exp(-t_click * 35.0)
    click = tone * 0.5
    cl_stereo = np.column_stack([click, click])
    wavfile.write(os.path.join(AUDIO_V3_DIR, "sfx_track_click.wav"), sr, (cl_stereo * 32767).astype(np.int16))

    # 4. Clapping Paws (0.22s double clap)
    t_clap = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
    noise = np.random.uniform(-0.6, 0.6, len(t_clap))
    e1 = np.where(t_clap < 0.10, np.sin(np.pi * t_clap / 0.10) ** 2, 0.0)
    e2 = np.where(t_clap > 0.11, np.sin(np.pi * (t_clap - 0.11) / 0.11) ** 2, 0.0)
    clap = noise * (e1 + e2) * 0.3
    cp_stereo = np.column_stack([clap, clap])
    wavfile.write(os.path.join(AUDIO_V3_DIR, "sfx_clapping.wav"), sr, (cp_stereo * 32767).astype(np.int16))

    # 5. Playful Toybox Music (42s bright glockenspiel & marimba chord melody)
    dur_bgm = 42.0
    t_bgm = np.linspace(0, dur_bgm, int(sr * dur_bgm), endpoint=False)
    bgm = np.zeros(len(t_bgm), dtype=np.float32)
    # Pentatonic toy melody notes: C4, E4, G4, A4, C5 (261, 329, 392, 440, 523 Hz)
    notes = [523.25, 392.0, 440.0, 329.63, 261.63, 392.0, 523.25, 659.25]
    beat_dur = 0.55
    num_beats = int(dur_bgm / beat_dur)
    for b in range(num_beats):
        n_freq = notes[b % len(notes)]
        st = int(b * beat_dur * sr)
        nd = min(len(bgm), st + int(beat_dur * sr * 1.5))
        n_len = nd - st
        if n_len > 0:
            tn = np.linspace(0, n_len / float(sr), n_len, endpoint=False)
            bell_env = np.exp(-tn * 4.5)
            harmonic1 = np.sin(2 * np.pi * n_freq * tn)
            harmonic2 = np.sin(2 * np.pi * n_freq * 2.0 * tn) * 0.4
            bgm[st:nd] += (harmonic1 + harmonic2) * bell_env * 0.28
    # Add gentle bass root
    bass_freq = 130.81  # C3
    bgm += np.sin(2 * np.pi * bass_freq * t_bgm) * 0.08
    bgm_stereo = np.column_stack([bgm, bgm])
    wavfile.write(os.path.join(AUDIO_V3_DIR, "toybox_music.wav"), sr, (bgm_stereo * 32767).astype(np.int16))


def build_final_audio_v3():
    print("🎵 Mixing Audio Master V3 for Mimi's Magic Toy Train...", flush=True)
    synthesize_toy_sfx()

    sr = 48000
    voice_path = os.path.join(AUDIO_V3_DIR, "narration_master.wav")
    music_path = os.path.join(AUDIO_V3_DIR, "toybox_music.wav")
    timing_path = os.path.join(AUDIO_V3_DIR, "timing_metadata.json")
    out_master_path = os.path.join(AUDIO_V3_DIR, "final_master_audio_v3.wav")

    # Load Voice
    _, voice_data = wavfile.read(voice_path)
    voice_f = voice_data.astype(np.float32) / 32768.0
    total_len = len(voice_f)
    duration_s = total_len / float(sr)

    # Load Music (loop to match duration)
    _, music_data = wavfile.read(music_path)
    music_f = music_data.astype(np.float32) / 32768.0
    repeats = int(math.ceil(total_len / float(len(music_f)))) + 1
    music_extended = np.tile(music_f, (repeats, 1))[:total_len]

    # Load Timing Metadata
    with open(timing_path, "r", encoding="utf-8") as f:
        timing_meta = json.load(f)

    # Ducking Envelope (-18.4 dB during dialogue)
    duck_curve = np.ones(total_len, dtype=np.float32) * (MUSIC_VOLUME * 0.70)
    for item in timing_meta:
        s_idx = int(item["start_time"] * sr)
        e_idx = min(total_len, int(item["end_time"] * sr))
        duck_curve[s_idx:e_idx] = MUSIC_VOLUME * 0.55

    mixed = np.copy(voice_f)
    mixed += music_extended * duck_curve[:, np.newaxis]

    # Overlay Synchronized SFX
    def overlay_sfx(sfx_name, timestamp_s, vol=SFX_VOLUME):
        sfx_file = os.path.join(AUDIO_V3_DIR, f"{sfx_name}.wav")
        if not os.path.exists(sfx_file):
            # Fallback to shared audio dir if exists
            sfx_file = os.path.join(CARTOON_DIR, "assets", "audio", f"{sfx_name}.wav")
        if not os.path.exists(sfx_file):
            return
        _, s_data = wavfile.read(sfx_file)
        s_f = (s_data.astype(np.float32) / 32768.0) * vol
        start_idx = int(timestamp_s * sr)
        end_idx = min(total_len, start_idx + len(s_f))
        actual_len = end_idx - start_idx
        if actual_len > 0:
            mixed[start_idx:end_idx] += s_f[:actual_len]

    # Scene 1: Kitten Footsteps
    for step_t in [1.2, 2.0, 2.8, 3.6, 4.4]:
        overlay_sfx("sfx_footstep", step_t, vol=0.14)

    # Scene 2: Train Pickup Whoosh
    overlay_sfx("sfx_pickup", 8.2, vol=0.25)

    # Scene 3: Track Placement "Click"
    overlay_sfx("sfx_track_click", 16.5, vol=0.30)

    # Scene 4: Whistle & Sparkle
    overlay_sfx("sfx_sparkle", 20.2, vol=0.28)
    overlay_sfx("sfx_train_whistle", 20.8, vol=0.35)
    # Clapping
    overlay_sfx("sfx_clapping", 24.2, vol=0.25)
    overlay_sfx("sfx_clapping", 25.8, vol=0.25)

    # Scene 4 & 5: Train Chugs
    for chug_t in np.arange(21.8, 33.0, 0.45):
        overlay_sfx("sfx_train_chug", chug_t, vol=0.16)

    # Scene 6: Outro Whistle & Sparkle
    overlay_sfx("sfx_sparkle", 37.5, vol=0.24)

    # Normalize to -1.0 dBFS Peak
    peak = np.max(np.abs(mixed))
    target_peak = 0.891
    if peak > target_peak:
        mixed = mixed * (target_peak / peak)

    out_16 = np.clip(mixed * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(out_master_path, sr, out_16)

    final_peak = np.max(np.abs(mixed))
    final_rms = np.sqrt(np.mean(mixed ** 2))
    print(f"✅ Master Audio V3 built: {out_master_path}", flush=True)
    print(f"   Duration: {duration_s:.2f}s | Peak: {final_peak:.3f} | RMS: {final_rms:.3f} (Zero Clipping)", flush=True)
    return out_master_path


if __name__ == "__main__":
    build_final_audio_v3()
