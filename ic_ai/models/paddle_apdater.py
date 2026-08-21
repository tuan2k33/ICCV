from paddleocr import TextDetection, TextRecognition
import numpy as np
import paddle


class PaddleOCRAdapter:
    def __init__(self, config, width=2160, height=2160, angle=0):
    # def __init__(self, config, width=2688, height=1512, angle=0):
        paddle.set_device(config['device'])
        self.config = config
        # try:
        mobile_det = config['mobile_det']
        mobile_rec = config['mobile_rec']

        if mobile_det and mobile_rec:
            self.model_rec = TextRecognition(model_name='PP-OCRv5_mobile_rec',model_dir=mobile_rec)
            self.model_det = TextDetection(model_name='PP-OCRv5_mobile_det', model_dir=mobile_det)
        # except:
        #     self.model_rec = TextRecognition(model_name=config['rec_model'])
        #     self.model_det = TextDetection(model_name=config['det_model'])
    def predict(self, input, text_rec_score_thresh=0.83):
        output = self.model_det.predict(input, batch_size=20)
        scores, texts, centers = [], [], []
        cropped_imgs = []
        centers_buffer = []
        idx_lst = [0]
        for out in output:
            dt_scores = np.array(out['dt_scores'])
            dt_polys = np.array(out['dt_polys'])
            img = np.array(out['input_img'])
            mask = dt_scores > text_rec_score_thresh
            filtered_polys = dt_polys[mask]
            filtered_scores = dt_scores[mask]
            len_keep = 0
            for poly, score in zip(filtered_polys, filtered_scores):
                if score < 0.7:
                    continue

                poly = poly.astype(int)
                x_min, y_min = np.min(poly[:, 0]), np.min(poly[:, 1])
                x_max, y_max = np.max(poly[:, 0]), np.max(poly[:, 1])
                crop = img[y_min:y_max, x_min:x_max]
                cx = int((x_min + x_max) / 2)
                cy = int((y_min + y_max) / 2)

                cropped_imgs.append(crop)
                centers_buffer.append([cx, cy])
                len_keep += 1
                if len(cropped_imgs) > 40:
                    output_rec = self.model_rec.predict(cropped_imgs, batch_size=20)
                    for tmp_rec, center in zip(output_rec, centers_buffer):
                        scores.append(tmp_rec['rec_score'])
                        texts.append(tmp_rec['rec_text'])
                        centers.append(center)
                    cropped_imgs = []
                    centers_buffer = []
            idx_lst.append(idx_lst[-1] + len_keep)
        if cropped_imgs:
            output_rec = self.model_rec.predict(cropped_imgs, batch_size=20)
            for tmp_rec, center in zip(output_rec, centers_buffer):
                scores.append(tmp_rec['rec_score'])
                texts.append(tmp_rec['rec_text'])
                centers.append(center)
            cropped_imgs = []
            centers_buffer = []
        results = []
        for i in range(len(idx_lst) - 1):
            start, end = idx_lst[i], idx_lst[i+1]
            results.append({
                "rec_scores": scores[start:end] if end > start else [0],
                "rec_texts": texts[start:end] if end > start else [""],
                "centers": centers[start:end] if end > start else [None],
            })
        return results
    
    def clear_cache(self):
        del self.model_det
        del self.model_rec
        paddle.device.cuda.empty_cache()
    

                

        

