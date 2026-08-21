import os
import subprocess

ROOT_FOLDER = "/ssd1/inventory_count/collect_data_2510"
VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm")

def get_video_duration(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        seconds = float(result.stdout.strip())
    except:
        seconds = 0.0

    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)

    return seconds, f"{h:02d}:{m:02d}:{s:02d}"

print("Video path | Duration (sec) | Duration (HH:MM:SS)")
print("-" * 80)

for root, _, files in os.walk(ROOT_FOLDER):
    for file in files:
        if file.lower().endswith(VIDEO_EXTENSIONS):
            video_path = os.path.join(root, file)
            sec, hms = get_video_duration(video_path)
            print(f"{video_path} | {sec:.2f} | {hms}")
