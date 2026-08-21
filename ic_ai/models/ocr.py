from paddleocr import PaddleOCR
from glob import glob
import paddle
import time
import re
from glob import glob
import numpy as np

paddle.set_device('cpu')

class OCR_AGENT:
    def __init__(self, width=3840, height=2880, angle=0):
        self.set_height_width(width=width, height=height)
        self.load_model()
        self.predictions = []
        self.angle = self.set_angle(angle)
    
    def set_angle(self, angle):
        self.angle = angle
    
    def set_height_width(self, height, width):
        h , w = height, width
        # self.x1, self.y1 =  0, int(h * 0.2)
        # self.x2, self.y2 = int(w * 0.8), int(h * 0.4)
        self.x1, self.y1 =  int(w * 0.3), 0
        self.x2, self.y2 = int(w * 0.7), int(h * 0.3)
    def transform_image(self, images):
        # if self.angle != 0:
        #     images = np.flip(images, axis=(1, 2))
        images = np.array(images)
        images = images[:, self.y1:self.y2, self.x1:self.x2, :]
        return images
    
    def load_model(self, light=True):
        if light:
            self.ocr = PaddleOCR(
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name="PP-OCRv5_mobile_rec",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False)
        else:
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                lang='en'
                )
    
    def get_texts(self, images):
        # images = self.transform_image(images)
        result = self.ocr.predict(images)
        output = []
        for res in result:
            scores = res['rec_scores']
            texts = res['rec_texts']
            for text, score in zip(texts, scores):
                if score > 0.95:
                    if re.search(r'[A-Za-z]', text) and re.search(r'\d', text):
                        output.append((text, score))
        return output
    
    def clear(self):
        self.predictions = []