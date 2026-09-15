import os

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_subtitles_file(timing_metadata, output_srt_path):
    os.makedirs(os.path.dirname(output_srt_path), exist_ok=True)
    with open(output_srt_path, "w", encoding="utf-8") as f:
        for idx, item in enumerate(timing_metadata, 1):
            start = format_srt_time(item["start_time"])
            end = format_srt_time(item["end_time"])
            text = item.get("text_en", "")
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")
    return output_srt_path
