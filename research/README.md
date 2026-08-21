tải dataset đã gán nhãn trên platform
initial file gồm images (folder "im") và labels (file json COCO format)

0.  coco_annotate.py    -> images: visualize labels lên trên ảnh
1.  coco_mask.py        -> images: crop ảnh, tô trắng background, labels: dời label theo crop và xoá "product package"
2.  coco2yolo.py        -> labels: chuyển format từ COCO (file json) sang YOLO (folder txt)
3.  split.py            -> images: chia folder thành 3 tập train-val-test
4.  train.py            -> train model yolo trên tập labeled, REQUIRE CUDA 12.8
5.  inference.py        -> test model trên tập mới

instances_default.json  -1-> masked.json        -2-> labels YOLO format
im (folder ảnh)         -1-> masked_images

labels + masked_images  -3-> data (folder)      -4-> kết quả train (trong terminal/folder runs/wandb)
data/images/test (hoặc tập ảnh test khác)       -5-> sinh label và trọng số

<!-- 
cấu trúc file  
# data/
# ├── config.yaml
# ├── images/
# │   ├── train/
# │   ├── val/
# │   └── test/
# └── labels/
#     ├── train/
#     ├── val/
#     └── test/
# im/ (file ban đầu)
# instances_default.json (file ban đầu)
# jameslahm/
# wandb/
# yolo/
# └── train/
#     ├── weights/
#     └── các files kết quả
# yolov10/
# yolov10-wandb/
# scripts/ (các file python)
-->