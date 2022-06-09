import os
import json
import PIL.Image
import PIL.ImageDraw
import numpy as np
from utils import create_dir, list_jsons_recursively
from image_utils import read_image_shape_as_dict


class labelme2coco(object):
    def __init__(self, labelme_folder='', save_json_path='./new.json'):
        """
        Args:
            labelme_folder: folder that contains labelme annotations and image files
            save_json_path: path for coco json to be saved
        """
        self.save_json_path = save_json_path
        self.images = []
        self.categories = []
        self.annotations = []
        self.label = []
        self.annID = 1
        self.height = 0
        self.width = 0

        self.name_to_cat = {
        'Rope':'rope',
        'ropa':'rope',
        'Helmet':'helmet',
        'Cell phone':'cellphone',
        'Cell Phone':'cellphone',
        'cell_phone':'cellphone',
        'Backpack':'backpack',
        'backpack':'backpack',
        'backback':'backpack',
        'back_pack':'backpack',
        'Survivor':'survivor',
        'survivor':'survivor',
        'survivior':'survivor',
        'survirvor':'survivor',
        'aurvivor':'survivor',
        'sruvivor':'survivor',
        'Cube':'cube',
        'Vent':'vent',
        'Drill':'drill',
        'Fire Extinguisher':'fire_extinguisher',
        'Fire extinguisher':'fire_extinguisher'
        }
        self.cat_to_id = {
        'rope':1,
        'helmet':2,
        'cellphone':3,
        'backpack':4,
        'survivor':5,
        'cube':6,
        'vent':7,
        'drill':8,
        'fire_extinguisher':9,
        }

        self.restricted = [
            'survivor',
            'backpack',
        ]
        # create save dir
        save_json_dir = os.path.dirname(save_json_path)
        create_dir(save_json_dir)

        # get json list
        _, labelme_json = list_jsons_recursively(labelme_folder)
        self.labelme_json = labelme_json

        self.save_json()

    def data_transfer(self):
        for num, json_path in enumerate(self.labelme_json):
            # print("fp {}".format(json_path))
            if os.path.exists(json_path) == False or os.stat(json_path).st_size == 0:
                continue

            with open(json_path, 'r') as fp:
                # load json
                data = json.load(fp)
                print("fp {}".format(fp))
#                (prefix, res) = os.path.split(json_path)
#                (file_name, extension) = os.path.splitext(res)
                if self.check_image(data, json_path):
                    self.images.append(self.image(data, num, json_path))
                else:
                    # print("SKIPPING")
                    continue
                for shapes in data['shapes']:
                    label = shapes['label']
                    if label == 'empty':
                        print("its empty!!")
                        continue
                    if label in self.name_to_cat.keys():
                        label = self.name_to_cat[label]
                        # print("label {}".format(label))
                    if label not in self.label:
                        self.categories.append(self.category(label))
                        self.label.append(label)
                    points = shapes['points']
                    self.annotations.append(self.annotation(points, label, num))
                    self.annID += 1
        print("labels {}".format(self.label))
        print("categories {}".format(self.categories))
        print("categories {}".format(self.category))

    def check_image(self, data, json_path):
        _, img_extension = os.path.splitext(data["imagePath"])
        image_path = json_path.replace(".json", img_extension)
        if os.path.exists(image_path):
            if image_path.find('august') > 0:
                for shapes in data['shapes']:
                    label = shapes['label']
                    if label in self.name_to_cat.keys():
                        label = self.name_to_cat[label]
                        print("label {}".format(label))
                        if label in self.restricted:
                            print("REMOVE")
                            # os.remove(json_path)
                            return False
            return True
        return False
            

    def image(self, data, num, json_path):
        image = {}
        # get image path
        _, img_extension = os.path.splitext(data["imagePath"])
        image_path = json_path.replace(".json", img_extension)
        img_shape = read_image_shape_as_dict(image_path)
        height, width = img_shape['height'], img_shape['width']

        image['height'] = height
        image['width'] = width
        image['id'] = int(num + 1)
        image['file_name'] = image_path

        self.height = height
        self.width = width

        return image

    def category_to_id(self, label):
        return self.cat_to_id[label]

    def category(self, label):
        category = {}
        category['supercategory'] = label
        category['id'] = self.category_to_id(label)
        category['name'] = label

        return category

    def annotation(self, points, label, num):
        annotation = {}
        annotation['iscrowd'] = 0
        annotation['image_id'] = int(num + 1)

        annotation['bbox'] = list(map(float, self.getbbox(points)))

        # coarsely from bbox to segmentation
        x = annotation['bbox'][0]
        y = annotation['bbox'][1]
        w = annotation['bbox'][2]
        h = annotation['bbox'][3]
        annotation['segmentation'] = [np.asarray(points).flatten().tolist()]

        annotation['category_id'] = self.getcatid(label)
        annotation['id'] = int(self.annID)
        # add area info
        annotation['area'] = (w-x)*(h-y)
        print("w-x {} h-y {}".format(w-x, h-y))
        print("area {}".format(annotation['area']))
        return annotation

    def getcatid(self, label):
        if label == 'empty':
            print("SUKA BLYAT ")
            exit()
        for categorie in self.categories:
            if label == categorie['name']:
                return categorie['id']
            # if label[1]==categorie['name']:
            #     return categorie['id']
        return -1

    def getbbox(self,points):
        # img = np.zeros([self.height,self.width],np.uint8)
        # cv2.polylines(img, [np.asarray(points)], True, 1, lineType=cv2.LINE_AA)
        # cv2.fillPoly(img, [np.asarray(points)], 1)
        polygons = points
        mask = self.polygons_to_mask([self.height, self.width], polygons)
        return self.mask2box(mask)

    def mask2box(self, mask):
        # np.where(mask==1)
        index = np.argwhere(mask == 1)
        rows = index[:, 0]
        clos = index[:, 1]

        left_top_r = np.min(rows)  # y
        left_top_c = np.min(clos)  # x

        right_bottom_r = np.max(rows)
        right_bottom_c = np.max(clos)

        return [left_top_c, left_top_r, right_bottom_c-left_top_c, right_bottom_r-left_top_r]  # [x1,y1,w,h] for coco box format

    def polygons_to_mask(self, img_shape, polygons):
        mask = np.zeros(img_shape, dtype=np.uint8)
        mask = PIL.Image.fromarray(mask)
        xy = list(map(tuple, polygons))
        PIL.ImageDraw.Draw(mask).polygon(xy=xy, outline=1, fill=1)
        mask = np.array(mask, dtype=bool)
        return mask

    def data2coco(self):
        data_coco = {}
        data_coco['images'] = self.images
        data_coco['categories'] = self.categories
        data_coco['annotations'] = self.annotations
        return data_coco

    def save_json(self):
        self.data_transfer()
        self.data_coco = self.data2coco()

        json.dump(self.data_coco, open(self.save_json_path, 'w', encoding='utf-8'), indent=4, separators=(',', ': '), cls=MyEncoder)


# type check when save json files
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)


if __name__ == "__main__":
    labelme_folder = "/media/mrs/Extreme SSD/DARPA/dataset/"
    save_json_path = "./full.json"
    labelme2coco(labelme_folder, save_json_path)
