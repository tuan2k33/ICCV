import csv
import os
import time
import re
from models.ocr import *
from models.product_id_reader import ProductIDReader
from collections import defaultdict
import torch
import pandas as pd
from utils.logger import get_logger

logger = get_logger('inventory.utils.get_pid')

def check_pattern(txt, pattern=r"\d{8}"):
    return re.fullmatch(pattern, txt[0]) is not None

def get_pid(o, frames, batch_size=16):
    """
    Processes a list of frames (images) to extract product IDs and their associated scores.
    Args:
        frames (list): List of image frames (numpy arrays).
    Returns:
        product_ids: List of extracted product IDs (text) for each frame.
        pid_scores: List of lists of scores associated with each product ID.
    """
    product_ids = []
    pid_scores = []
       
    result = o.predict(frames, text_rec_score_thresh=0.6, batch_size=batch_size)
    text_list = [item["rec_texts"] for item in result]
    score_list = [item["rec_scores"] for item in result]
    for texts, scores in zip(text_list, score_list):
        dict_score_text = defaultdict(list)
        for txt, scr in zip(texts, scores):
            if check_pattern([txt]):
                dict_score_text[txt].append(scr)
        if dict_score_text:
            max_len = max(len(v) for v in dict_score_text.values())
            t2 = [(k, v) for k, v in dict_score_text.items() if len(v) == max_len]
        else:
            t2 = [("",[])]
        product_ids.append(t2[0][0])
        pid_scores.append(t2[0][1])
    return product_ids, pid_scores




