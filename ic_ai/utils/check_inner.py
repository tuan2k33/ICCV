
import torch
import pandas as pd
from utils.logger import get_logger
import numpy as np 

logger = get_logger('inventory.utils.check_inner')

def check_inner(classify, frames):
    # for key, value in data_dict.items():
        # if key != 'BE-110-2': continue
        # if value["score"] == 0:
        # front_path = value["front"]

        # img = cv2.imread(front_path)
        # img_tensor = torch.from_numpy(img).float()
        # img_tensor = img_tensor.unsqueeze(0)
    if isinstance(frames, list):
        imgs_tensor = torch.stack([
            torch.from_numpy(img).float() for img in frames
        ])
    elif isinstance(frames, np.ndarray):
        imgs_tensor = torch.from_numpy(frames).float()
    elif isinstance(frames, torch.Tensor):
        imgs_tensor = frames.float()
    else:
        raise TypeError("frames phải là list[np.ndarray], np.ndarray hoặc torch.Tensor")
    
    cls_pred, scores, max_score = classify.predict(imgs_tensor)

    list_pred = [int(p) for p in cls_pred]
    list_score = [float(s) for s in max_score]

        # value["score_empty"] = max_score[0]
        # value["empty"] = int(cls_pred[0])    
        # logger.info('Classified: %s',front_path)
    return list_pred, list_score


    




