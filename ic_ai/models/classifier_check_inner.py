from torchvision import models, transforms
from torchvision.transforms.functional import crop, rotate
import torch
import torch.nn.functional as F
import cv2

class_names = ['0', '1', '2']
class Classifier:
    _instances = {}
    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    def __init__(self, w_path, width=2160, height=2160, angle=1):
    # def __init__(self, w_path, width=2688, height=1512, angle=1):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.load_model(w_path)
        self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                        std=[0.229, 0.224, 0.225])
        ])
        self.set_height_width(width=width, height=height)
        self.predictions = []
        self.set_angle(angle)
    
    def set_angle(self, angle):
        self.angle = angle
    
    def set_height_width(self, height, width):
        # self.top, self.left = int(height * 0.4), int(width * 0.2)
        # self.width, self.height= int(width * 0.6), int(height * 0.5)
        self.top, self.left = int(height * 0.3), int(width * 0.3)
        self.width, self.height= int(width * 0.4), int(height * 0.6)
    
    def get_target_zone(self):
        return [self.top, self.left, self.width, self.height]

    def transform_image(self, images):
        # print(images.shape)
        images = images.permute(0, 3, 1, 2) / 255.0  
        # print(images.shape)
        # exit()
        # if self.angle != 0:
        #     images = rotate(images, self.angle)
        images = crop(images, self.top, self.left, self.height, self.width)
        # images = images.permute(0,2,3,1) * 255.0

        # cv2.imwrite('test_.png',images[0].cpu().numpy().astype(int))
        # exit()
        images = self.transform(images)
        images = images.to(self.device)
        return images
    
    def load_model(self, weight_path):
        model = models.resnet50(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, len(class_names))
        model.load_state_dict(torch.load(weight_path, map_location=self.device,weights_only=False))
        model.to(self.device).eval()
        return model
    
    def predict(self, images):
        images = self.transform_image(images)
        with torch.no_grad():
            outputs = self.model(images)
            softmax_out = F.softmax(outputs, dim=1)
            preds = torch.argmax(outputs, dim=1).tolist()
            labels = [class_names[i] for i in preds]
            scores = [softmax_out[j, i].item() for j, i in enumerate(preds)]
            self.predictions.extend(labels)
        return labels, softmax_out[0].squeeze().tolist(), scores
    
    def clear(self):
        self.predictions = []

    def clear_cache(self):
        del self.model
        torch.cuda.empty_cache()



