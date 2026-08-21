from paddleocr import TextDetection, TextRecognition
import numpy as np
import paddle

class ProductIDReader:
    def __init__(self, config, width=2160, height=2160, angle=0):
    # def __init__(self, config, width=2688, height=1512, angle=0):
        paddle.set_device(config['device'])
        self.config = config
        # try:
        server_det = config['server_det']
        server_rec = config['server_rec']
        if server_det and server_rec:
            self.model_rec = TextRecognition(model_name='PP-OCRv5_server_rec', model_dir=server_rec)
            self.model_det = TextDetection(model_name='PP-OCRv5_server_det', model_dir=server_det)
        # except:
        #     self.model_rec = TextRecognition(model_name="PP-OCRv5_server_rec")
        #     self.model_det = TextDetection(model_name="PP-OCRv5_server_det")
        self.set_height_width(width=width, height=height)

    def set_height_width(self, height,width):
        h , w = height, width
        self.x1, self.x2 = int(w * 0.2), int(w * 0.8)
        self.y1, self.y2 = int(0.2*h), int(h*0.8)
       
    
    def transform_image(self, images):
        images = np.array(images)
        images = images[:, self.y1:self.y2, self.x1:self.x2, :]
        return images
    
    def predict(self, input, text_rec_score_thresh=0.5, batch_size=1):
        input = self.transform_image(input)
        input = [input[i] for i in range(input.shape[0])]
        output = self.model_det.predict(input, batch_size=batch_size)

        scores, texts = [], []
        cropped_imgs = []
        idx_lst = [0]
        results = []
        for out in output:
            mask = np.array(out['dt_scores']) > text_rec_score_thresh
            filtered_polys = np.array(out['dt_polys'])[mask]
            img = np.array(out['input_img'])

            for poly in filtered_polys:
                poly = poly.astype(int)
                x_min = np.min(poly[:, 0])
                y_min = np.min(poly[:, 1])
                x_max = np.max(poly[:, 0])
                y_max = np.max(poly[:, 1])
                crop = img[y_min:y_max, x_min:x_max]
                cropped_imgs.append(crop)
                
                if len(cropped_imgs) > batch_size:
                    # output_rec = self.model_rec.predict(cropped_imgs, batch_size=20)
                    output_rec = self.model_rec.predict(cropped_imgs, batch_size=batch_size)
                    for tmp_rec in output_rec:
                        scores.append(tmp_rec['rec_score']) #he
                        texts.append(tmp_rec['rec_text']) #he
                        # print('text',texts)
                    cropped_imgs = []
            idx_lst.append(idx_lst[-1]+len(filtered_polys))

        # output_rec = self.model_rec.predict(cropped_imgs, batch_size=20)
        output_rec = self.model_rec.predict(cropped_imgs, batch_size=batch_size)
        for tmp_rec in output_rec:
            scores.append(tmp_rec['rec_score']) #he
            texts.append(tmp_rec['rec_text']) #he
        cropped_imgs = []
        results = []
        for i, idx in enumerate(idx_lst[:-1]):
            results.append({
                "rec_scores": scores[idx_lst[i]:idx_lst[i+1]] if idx_lst[i+1] - idx_lst[i] > 0 else [0],
                "rec_texts": texts[idx_lst[i]:idx_lst[i+1]] if idx_lst[i+1] - idx_lst[i] > 0 else [""]
            })
        return results
    
    def clear_cache(self):
        del self.model_det
        del self.model_rec
        paddle.device.cuda.empty_cache()
        
