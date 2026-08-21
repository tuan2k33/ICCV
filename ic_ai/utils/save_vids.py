import os
import subprocess
from utils.get_frame_position import *

def save_videos(ret, 
                video_path = "/ssd1/collect_data_2009/SD_2/DJI_20250920134142_0001_D.MP4",
                output_path = "/ssd1/thaokb/inventory-count-ai/outputs5", fps=30):

    for [c,f,t], key in ret:
        start=min(c[0],f[0],t[0])-fps
        end=max(c[0],f[0],t[0])+fps
        
        os.makedirs(os.path.join(output_path, key), exist_ok=True)
        # Use ffmpeg to extract the video segment
        v = os.path.join(output_path, key, f"{key}.mp4")
        process = subprocess.run([
            'ffmpeg',
            '-y', 
            '-hwaccel', 'cuda',
            '-ss', str(start/fps),
            '-t', str((end - start)/fps),
            '-i', video_path,
            '-c', 'copy',
            v
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)