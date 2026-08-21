import os
import shutil
import copy
import requests
import torch
import time
import ffmpeg
import pandas as pd
import json
import queue
from threading import Thread
from tqdm import tqdm
from models.paddle_apdater import PaddleOCRAdapter
from models.classifier import Classifier
from utils.process_raw import process_csv_raw
from utils.get_frame_position import *
from utils.reader import load_yaml
from utils.save_frame import save_frames_by_metadata
import subprocess
from utils.logger import get_logger
import logging
import argparse
from utils.save_vids import save_videos
from utils.video_reader import VideoReader

logger = logging.getLogger(__name__)

BATCH_SIZE = 16
BATCH_SIZE_OCR = 16
BATCH_SIZE_PID = 1


class VideoProcessing:
    def __init__(self, config_classifier, config_ocr):
        model_path = config_classifier['model_path']
        model_link = config_classifier.get('model_link')

        if not os.path.exists(model_path):
            if not model_link:
                logger.error(f"Model file not found at '{model_path}' and no 'model_link' provided.")
                raise FileNotFoundError(
                    f"Model file not found at '{model_path}' and no 'model_link' provided in config."
                )

            logger.warning(f"Model not found at '{model_path}'.")
            logger.info(f"Downloading from '{model_link}'...")

            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            try:
                response = requests.get(model_link, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))

                with open(model_path, 'wb') as f, tqdm(
                    desc=os.path.basename(model_path),
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))

                print(f"Download complete. Model saved to '{model_path}'.")

            except requests.exceptions.RequestException as e:
                if os.path.exists(model_path):
                    os.remove(model_path)
                raise ConnectionError(f"Failed to download model from {model_link}. Error: {e}")

        self.cls_model = Classifier(w_path=model_path)
        self.text_model = PaddleOCRAdapter(config=config_ocr)
        self.df = {
            "frame_idx": [],
            "label": [],
            "ocr": [""],
            "score": [""],
            "ocr_center": [None],
        }
        self.ocr_queue = queue.Queue(maxsize=10)
        self.ocr_thread = None

    def _ocr_worker(self):
        while True:
            try:
                batch = self.ocr_queue.get(timeout=10.0)
                if batch is None:
                    self.ocr_queue.task_done()
                    break
                indices, images = batch
                results = self.text_model.predict(
                    input=images,
                    text_rec_score_thresh=0.5
                )
                for j, idx in enumerate(indices):
                    if j < len(results):
                        self.df["score"][idx] = results[j]["rec_scores"]
                        self.df["ocr"][idx] = results[j]["rec_texts"]
                        self.df["ocr_center"][idx] = results[j]["centers"]
                self.ocr_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.exception(f"OCR Worker Error: {e}")
                self.ocr_queue.task_done()

    def reset(self):
        self.df = {
            "frame_idx": [],
            "label": [],
            "ocr": [""],
            "score": [""],
            "ocr_center": [None],
        }
        self.ocr_queue = queue.Queue(maxsize=10)
        self.ocr_thread = None

    def start_ocr_thread(self):
        self.ocr_thread = Thread(target=self._ocr_worker, daemon=True)
        self.ocr_thread.start()

    def stop_ocr_thread(self):
        self.ocr_queue.put(None)
        self.ocr_thread.join()  # wait until worker processes all queued batches + sentinel

    def get_video_metadata(self, video_path):
        probe = ffmpeg.probe(video_path)
        stream = probe['streams'][0]
        width = stream['width']
        height = stream['height']
        angle = int(stream.get('tags', {}).get('rotate', 0))
        return width, height, angle

    def infer_video(self, config_video):
        video_path = config_video['input']
        vr = VideoReader(video_path)

        width, height, angle = self.get_video_metadata(video_path)

        self.cls_model.set_height_width(width=width, height=height)
        self.cls_model.set_angle(angle)
        total_frames = len(vr)

        self.df["frame_idx"] = []
        self.df["label"] = []
        self.df["score"] = [""] * total_frames
        self.df["ocr"] = [""] * total_frames
        self.df["ocr_center"] = [None] * total_frames

        self.start_ocr_thread()
        ocr_buffer = []

        for batch_start in tqdm(range(0, total_frames, BATCH_SIZE), desc="Processing frames"):
            batch_end = min(batch_start + BATCH_SIZE, total_frames)
            frame_indices = list(range(batch_start, batch_end))

            frames = vr.get_batch(frame_indices)  # (N, H, W, 3)
            if angle != 0:
                frames = torch.flip(frames, dims=[1, 2])
            h, w = frames.shape[1], frames.shape[2]
            top = int(0.1 * h)
            bottom = int(0.4 * h)
            crops = frames[:, top:bottom, :, :]  # (N, crop_h, W, 3)

            cls_preds = list(self.cls_model.predict(crops))
            self.df["frame_idx"].extend(frame_indices)

            half = len(cls_preds) // 2
            for h_start, h_end in [(0, half), (half, len(cls_preds))]:
                if h_start == h_end:
                    continue
                if 'code' in cls_preds[h_start:h_end]:
                    for k in range(h_start, h_end):
                        cls_preds[k] = 'code'
                for j in range(h_end - h_start):
                    frame_idx = batch_start + h_start + j
                    if cls_preds[h_start + j] == 'code':
                        img = crops[h_start + j].cpu().numpy()[:, :, ::-1]
                        ocr_buffer.append((frame_idx, img))
                    if len(ocr_buffer) >= BATCH_SIZE_OCR:
                        ocr_indices, ocr_images = zip(*ocr_buffer)
                        self.ocr_queue.put((list(ocr_indices), list(ocr_images)))
                        ocr_buffer = []

            self.df["label"].extend(cls_preds)

        if ocr_buffer:
            indices, images = zip(*ocr_buffer)
            self.ocr_queue.put((list(indices), list(images)))

        self.stop_ocr_thread()

        self.cls_model.clear_cache()
        self.text_model.clear_cache()

        df_for_save = pd.DataFrame(self.df)
        df_for_save["score"] = df_for_save["score"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )
        df_for_save["ocr"] = df_for_save["ocr"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )
        df_for_save["ocr_center"] = df_for_save["ocr_center"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
        )
        df_for_save.to_csv(config_video['raw_csv'], index=False)
        logger.info(f"Hoàn thành csv gốc! Kết quả lưu tại {config_video['raw_csv']}")
        return df_for_save, vr


def split_video_lr(video_path: str) -> tuple[str, str]:
    base = os.path.splitext(video_path)[0]
    left_path = f"{base}_L.mp4"
    right_path = f"{base}_R.mp4"
    for out_path, crop in [(left_path, "crop=trunc(iw/2):ih:0:0"), (right_path, "crop=trunc(iw/2):ih:trunc(iw/2):0")]:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vf", crop,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "copy", out_path],
            capture_output=True, text=True, check=True
        )
    return left_path, right_path


def concat_videos(video_paths_list: list = [], output_path: str = "", mode: int = 1) -> str:
    if not video_paths_list:
        return ""

    valid_videos = []
    for video_path in video_paths_list:
        if not os.path.exists(video_path):
            logger.warning(f"Video file not found: {video_path}")
            continue

        try:
            probe = ffmpeg.probe(video_path)

            video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
            if not video_streams:
                logger.warning(f"No video stream found in: {video_path}")
                continue

            duration = float(probe['format'].get('duration', 0))
            if duration <= 0:
                logger.warning(f"Invalid duration for video: {video_path}")
                continue

            valid_videos.append(video_path)
            logger.info(f"Valid video: {video_path} (duration: {duration:.2f}s)")

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error checking video {video_path}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error checking video {video_path}: {e}")
            continue

    if not valid_videos:
        logger.error("No valid videos found to concatenate")
        return ""

    if len(valid_videos) == 1 and mode == 1:
        logger.info("Only one valid video, returning original path")
        return valid_videos[0]

    if not output_path:
        current_time = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.path.dirname(valid_videos[0]), f"{current_time}.mp4")

    temp_files = []
    if mode == 2:
        concat_list = []
        for video_path in valid_videos:
            try:
                left, right = split_video_lr(video_path)
                concat_list.extend([left, right])
                temp_files.extend([left, right])
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to split {video_path}: {e.stderr}")
                return ""
    else:
        concat_list = valid_videos

    list_file = output_path + ".txt"
    try:
        with open(list_file, "w") as f:
            for v in concat_list:
                f.write(f"file '{v}'\n")
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path
        ]

        logger.info(f"Concatenating {len(concat_list)} videos to: {output_path}")
        subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
        logger.info(f"Successfully concatenated videos to: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg concatenation failed: {e.stderr}")
        return ""
    except Exception as e:
        logger.error(f"Error during video concatenation: {e}")
        return ""
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)


def get_inventory_informations(video_input: list[str], config: dict, output_path: str = "outputs", mode: int = 1) -> dict:
    if not video_input:
        return ""

    config = copy.deepcopy(config)
    video_path = concat_videos(video_input, mode=mode)
    if not video_path:
        return ""

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    timestamp = int(time.time() * 100)
    result_folder = f"{video_name}_{timestamp}_result"
    result_path = os.path.join(output_path, result_folder)
    os.makedirs(result_path, exist_ok=True)

    video_log_file = os.path.join(result_path, f"{video_name}_{timestamp}_result.log")
    video_logger_name = f"VideoProcessing_{video_name}_{timestamp}"

    logger = get_logger(video_logger_name, log_file=video_log_file)

    config['video']['input'] = video_path
    config['video']['processed_csv'] = os.path.join(result_path, config['video']['processed_csv'])
    config['video']['raw_csv'] = os.path.join(result_path, config['video']['raw_csv'])

    global BATCH_SIZE
    global BATCH_SIZE_OCR
    global BATCH_SIZE_PID

    BATCH_SIZE = config.get('batch_size', 16)
    BATCH_SIZE_OCR = config.get('batch_size_ocr', 16)
    BATCH_SIZE_PID = config.get('batch_size_pid', 1)

    start = time.time()
    logger.info(f"Bắt đầu xử lý video: {video_path}")

    vidp = VideoProcessing(config_classifier=config['classifier'], config_ocr=config['ocr'])
    vidp.reset()

    t0 = time.time()
    df, vr = vidp.infer_video(config_video=config['video'])
    logger.info("[Timing] Decode + Classify + OCR toàn bộ: %.2f s", time.time() - t0)

    t1 = time.time()
    shape = vr.get_shape()  # (n_frames, H, W, 3)
    fps = vr.get_fps()
    img_h = shape[1]
    target_y = img_h // 4 if mode == 1 else img_h // 3
    df_processed = process_csv_raw(df, config['video']['processed_csv'], score_threshold=0,
                                   img_width=shape[2])
    output_frames = get_all_codes(df_processed, fps=fps, target_y=target_y)
    logger.info("[Timing] Xử lý logic (process_csv + get_all_codes): %.2f s", time.time() - t1)

    t2 = time.time()
    save_videos(output_frames, video_path=video_path, output_path=output_path)
    w, h, angle = vidp.get_video_metadata(video_path=video_path)
    dict_total = save_frames_by_metadata(
        vr,
        frame_info_list=output_frames,
        timestamp=timestamp,
        output_root=output_path,
        output_json=result_path,
        batch_size=BATCH_SIZE_PID,
        angle=angle,
        config=config
    )
    logger.info("[Timing] Lưu video + ảnh (save_videos + save_frames): %.2f s", time.time() - t2)

    logger.info("[Timing] Tổng toàn bộ pipeline: %.2f s", time.time() - start)

    dest = os.path.join(result_path, os.path.basename(video_path))
    if os.path.abspath(video_path) != os.path.abspath(dest):
        is_original = os.path.abspath(video_path) in [os.path.abspath(p) for p in video_input]
        if is_original:
            shutil.copy2(video_path, dest)
            logger.info("Copied original video to %s", dest)
        else:
            os.rename(video_path, dest)
            logger.info("Moved processed video to %s", dest)

    return dict_total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process videos to get inventory information.')
    parser.add_argument('--video_input', nargs='+', required=True,
                        help='One or more video file paths.')
    parser.add_argument('--output_path', type=str, default='outputs',
                        help='Path to the output directory.')
    parser.add_argument('--config', type=str, default='configs/config.yaml',
                        help='Path to the configuration file.')
    parser.add_argument('--mode', type=int, default=1, choices=[1, 2],
                        help='Mode 1: normal concat. Mode 2: split each video L/R then concat.')
    args = parser.parse_args()

    config = load_yaml(args.config)

    get_inventory_informations(video_input=args.video_input,
                               config=config,
                               output_path=args.output_path,
                               mode=args.mode)
