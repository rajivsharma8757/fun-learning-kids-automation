import os
import sys
import time
import subprocess
import json
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import AUDIO_DIR, VOICE_NARRATOR

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def generate_segment_with_retry(text, voice, out_mp3, max_retries=6):
    for attempt in range(1, max_retries + 1):
        if os.path.exists(out_mp3):
            try:
                os.remove(out_mp3)
            except Exception:
                pass
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", out_mp3
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode == 0 and os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 3000:
                return True
        except Exception as e:
            print(f"Segment attempt {attempt} failed: {e}")
        time.sleep(2 + attempt * 2)
    return False

class VoiceEngine:
    def __init__(self, target_sr=48000):
        self.target_sr = target_sr

    def generate_narration(self, script_scenes, voice=VOICE_NARRATOR, output_wav=None, output_json=None):
        if output_wav is None:
            output_wav = os.path.join(AUDIO_DIR, "narration_master.wav")
        if output_json is None:
            output_json = os.path.join(AUDIO_DIR, "timing_metadata.json")

        all_segments = []
        current_time = 0.0
        timing_records = []

        for idx, item in enumerate(script_scenes):
            seg_mp3 = os.path.join(AUDIO_DIR, f"seg_{idx+1}.mp3")
            seg_wav = os.path.join(AUDIO_DIR, f"seg_{idx+1}.wav")

            ok = generate_segment_with_retry(item["text_hi"], voice, seg_mp3)
            if not ok:
                raise RuntimeError(f"Voice generation failed for scene {idx+1}")

            subprocess.run(["ffmpeg", "-y", "-i", seg_mp3, "-ar", str(self.target_sr), "-ac", "2", seg_wav],
                           check=True, capture_output=True)

            sr, raw = wavfile.read(seg_wav)
            samples = raw.astype(np.float32) / 32768.0

            # Trim digital silence
            energy = np.abs(samples[:, 0]) + np.abs(samples[:, 1])
            thresh = 0.015
            non_silent = np.where(energy > thresh)[0]
            if len(non_silent) > 0:
                start_idx = max(0, non_silent[0] - int(self.target_sr * 0.04))
                end_idx = min(samples.shape[0], non_silent[-1] + int(self.target_sr * 0.04))
                samples = samples[start_idx:end_idx]

            # Loudness normalization to 0.88 peak (-1.1 dBFS)
            peak = np.max(np.abs(samples))
            if peak > 0:
                samples = samples * (0.88 / peak)

            # Micro-fades (15ms)
            fade_len = int(self.target_sr * 0.015)
            fade_in = np.linspace(0.0, 1.0, fade_len)[:, np.newaxis]
            fade_out = np.linspace(1.0, 0.0, fade_len)[:, np.newaxis]
            samples[:fade_len] *= fade_in
            samples[-fade_len:] *= fade_out

            seg_duration = len(samples) / self.target_sr
            pause_len = int(self.target_sr * 0.25)
            pause = np.zeros((pause_len, 2), dtype=np.float32)

            rec = dict(item)
            rec["start_time"] = round(current_time, 3)
            rec["end_time"] = round(current_time + seg_duration, 3)
            rec["duration"] = round(seg_duration, 3)
            current_time = round(rec["end_time"] + 0.25, 3)

            timing_records.append(rec)
            all_segments.append(samples)
            all_segments.append(pause)

        master_samples = np.concatenate(all_segments, axis=0)
        master_int16 = (master_samples * 32767.0).clip(-32768, 32767).astype(np.int16)

        wavfile.write(output_wav, self.target_sr, master_int16)
        total_duration = len(master_samples) / self.target_sr

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(timing_records, f, ensure_ascii=False, indent=2)

        return output_wav, timing_records, total_duration
