# AUTOGENERATED! DO NOT EDIT! File to edit: nb_data.dataset.ipynb (unless otherwise specified).

__all__ = ['DataFrameImageDataset']

# Cell
from ..utils.general import t2p
import cv2
import matplotlib.pyplot as plt
import math
import PIL
import torch
from torch.utils.data import Dataset
from collections import Counter

# Cell
class DataFrameImageDataset(Dataset):
    '''Build an image dataset from a dataframe.

    Images are opened as numpy arrays (cv2) so that albumentation
    transformations can be used.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing image paths and corresponding labels (optional)

    img_col : str
        Name of df column containing image paths

    label_col : str; optional
        Name of df column containing image labels.
        If None, ´self.label_col´ are all zeros.

    root : str; optional
        Top-level directory that gets prepended to image paths

    img_transform : callable; optional
        Composition of albumentation transforms (or any transforms that work on numpy arrays)

    label_names : list; optional
        List of unique label names. Order of list determines what integer a label is mapped to.
        If None, ´self.label_names´ are determined by ´self.label´.

    Attributes
    ----------
    label_to_int : dict
        Mapping between label names and integers.

    int_to_label : dict
        Mapping between integers and labels.

    num_labels : int
        Number of unique labels
    '''
    def __init__(
        self,
        df,
        img_col,
        label_col=None,
        root="./",
        img_transform=None,
        label_names=None
    ):
        self.imgs = list(df[img_col])
        self.labels = list(df[label_col]) if label_col is not None else [0,]*len(self.imgs)
        self.root = root
        self.img_transform = img_transform
        self.label_names = label_names if label_names is not None else sorted(set(self.labels))
        self.label_to_int = {k:v for v, k in enumerate(self.label_names)}
        self.int_to_label = {v: k for k, v in self.label_to_int.items()}
        self.num_labels = len(self.label_names)

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img = cv2.imread(os.path.join(self.root, self.imgs[idx]))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        label = self.label_to_int[self.labels[idx]]
        if self.img_transform:
            img = self.img_transform(image=img)["image"]
        return img, label

    def __repr__(self):
        info = ""
        info += f"Number of images\t: {self.__len__()}\n"
        info += f"Number of labels\t: {len(self.label_to_int)}\n"
        for k, v in self.label_to_int.items():
            info += f"-> {k} ({Counter(self.labels)[k]})\n"
        if self.img_transform:
            info += "\nImage transformations:\n"
            info += f"{self.img_transform.__repr__()}\n"
        return info

    def get_labels(self):
        '''Label getter function required for compatibility with various modules'''
        return self.labels

    def get_n_items(self, n, random=False):
        idxs = np.arange(n)
        if random:
            idxs = np.random.choice(self.__len__(), n, replace=False)

        items = list()
        for idx in idxs:
            items.append(self.__getitem__(idx))

        return items

    def convert_to_pil_img(self, img):
        if isinstance(img, PIL.Image.Image):
            return img
        elif isinstance(img, np.ndarray):
            return PIL.Image.fromarray(img)
        elif isinstance(img, torch.Tensor):
            return t2p(img)
        else:
            raise TypeError(f"Conversion from {type(img)} to pillow image not possible")

    def show_n_items(self, n=9, random=False, figsize=(10, 10)):
        items = self.get_n_items(n, random)
        fig, axes = plt.subplots(math.ceil(n/3), 3, figsize=figsize)
        for ax, item in zip(axes.flatten(), items):
            img, label = self.convert_to_pil_img(item[0]), self.int_to_label[item[1]]
            ax.set_title(label)
            ax.imshow(img)
            ax.axis('off')