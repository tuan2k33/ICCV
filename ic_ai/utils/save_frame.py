import numpy as np
import cv2
import os
from utils.get_pid import get_pid
from models.product_id_reader import ProductIDReader
import torch
import json
from utils.logger import get_logger
from models.classifier_check_inner import Classifier
from utils.check_inner import check_inner

def aggregate_results(frame_info_list, dict_code, dict_front, dict_top):
    dict_total = {}
    for bin_code in set(info[1] for info in frame_info_list):
        dict_total[bin_code] = {
            "code": [],
            "front": [],
            "top": [],
            "video": [],
            "product_id": None,
            "score_pid": None,
            "empty": None,
            "score_empty": None
        }

    for info in frame_info_list:
        code_frame, front_frame, top_frame = info[0][0][0], info[0][1][0], info[0][2][0]
        bin_code = info[1]

        name = dict_code[code_frame]["path"].split("_")[-2]
        dict_total[bin_code][name].append(dict_code[code_frame]["path"])

        name = dict_front[front_frame]["path"].split("_")[-2]
        dict_total[bin_code][name].append(dict_front[front_frame]["path"])

        name = dict_top[top_frame]["path"].split("_")[-2]
        dict_total[bin_code][name].append(dict_top[top_frame]["path"])

        video_path = f"{'/'.join(dict_code[code_frame]['path'].split('/')[:-1])}/{bin_code}.mp4"
        dict_total[bin_code]["video"].append(video_path)

        dict_total[bin_code]["product_id"] = dict_front[front_frame].get("product_id")
        dict_total[bin_code]["score_pid"] = dict_front[front_frame].get("score_pid")
        dict_total[bin_code]["empty"] = dict_front[front_frame].get("empty")
        dict_total[bin_code]["score_empty"] = dict_front[front_frame].get("score_empty")
    return dict_total


def save_image(info: tuple[np.ndarray, str], logger: None) -> None:
    image, filename = info
    cv2.imwrite(filename, image)
    if logger:
        logger.info("Saved: %s", filename)

 
def save_frames_by_metadata(vr, timestamp: int, frame_info_list: list, output_root: str, output_json: str, batch_size: int, angle: int, config: dict) -> dict:
    video_name = output_json.split("/")[-1]
    video_logger = get_logger("SaveFrame", log_file=f"{output_json}/{video_name}.log")

    def to_bgr(tensor):
        if angle != 0:
            tensor = torch.flip(tensor, dims=[0, 1])
            tensor = torch.flip(tensor, dims=[2])
        return tensor[:, :, :, [2, 1, 0]].cpu().numpy()

    o = ProductIDReader(config=config['ocr'])
    classify_empty = Classifier(w_path='weights/resnet50_trained_new_classify_2.pth')

    meta = []
    for info in frame_info_list:
        bin_code = info[1]
        os.makedirs(os.path.join(output_root, bin_code), exist_ok=True)
        code_path  = f"{output_root}/{bin_code}/{bin_code}_{info[0][0][1]}_{timestamp}.jpg"
        front_path = f"{output_root}/{bin_code}/{bin_code}_{info[0][1][1]}_{timestamp}.jpg"
        top_path   = f"{output_root}/{bin_code}/{bin_code}_{info[0][2][1]}_{timestamp}.jpg"

        # save code
        img = to_bgr(vr.get_batch([info[0][0][0]]))[0]
        save_image((img, code_path), video_logger)

        # save top
        img = to_bgr(vr.get_batch([info[0][2][0]]))[0]
        save_image((img, top_path), video_logger)

        meta.append({'code_path': code_path, 'front_path': front_path, 'top_path': top_path,
                     'front_frame': info[0][1][0]})

    # front in batches (PID + empty inference)
    front_frames = [m['front_frame'] for m in meta]
    for i in range(0, len(front_frames), batch_size):
        batch = front_frames[i:i + batch_size]
        lst_image = to_bgr(vr.get_batch(batch))
        product_ids, pid_scores = get_pid(o, lst_image)
        preds, scores = check_inner(classify_empty, lst_image)

        for j, (image, pid, score_pid, pred, score_empty) in enumerate(
                zip(lst_image, product_ids, pid_scores, preds, scores)):
            idx = i + j
            save_image((image, meta[idx]['front_path']), video_logger)
            meta[idx]['product_id'] = pid if pred != 2 else ""
            meta[idx]['score_pid'] = 0 if np.isnan(score_pid).all() or pred == 2 else np.mean(score_pid)
            meta[idx]['empty'] = pred
            meta[idx]['score_empty'] = score_empty

    dict_total = {bin_code: {"code": [], "front": [], "top": [], "video": [],
                             "product_id": None, "score_pid": None, "empty": None, "score_empty": None}
                  for bin_code in set(info[1] for info in frame_info_list)}

    for info, m in zip(frame_info_list, meta):
        bin_code = info[1]
        dict_total[bin_code]["code"].append(m['code_path'])
        dict_total[bin_code]["front"].append(m['front_path'])
        dict_total[bin_code]["top"].append(m['top_path'])
        dict_total[bin_code]["video"].append(f"{output_root}/{bin_code}/{bin_code}.mp4")
        dict_total[bin_code]["product_id"] = m.get('product_id')
        dict_total[bin_code]["score_pid"] = m.get('score_pid')
        dict_total[bin_code]["empty"] = m.get('empty')
        dict_total[bin_code]["score_empty"] = m.get('score_empty')

    os.makedirs(os.path.dirname(f"{output_root}/dict_total.json"), exist_ok=True)
    with open(f"{output_json}/dict_total.json", "w", encoding="utf-8") as f:
        json.dump(dict_total, f, ensure_ascii=False, indent=4)

    return dict_total




