# AUTOGENERATED! DO NOT EDIT! File to edit: nb_train.best_practices.ipynb (unless otherwise specified).

__all__ = ['LiuProcedure', 'LasserProcedure', 'ValleProcedure', 'XuProcedure', 'get_inference_tfms', 'get_train_tfms']

# Cell
import pandas as pd
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2
import torch
from pl_bolts.optimizers.lr_scheduler import LinearWarmupCosineAnnealingLR
import torch.nn.functional as F


# Cell
class LiuProcedure():
    '''Liu et al. (https://arxiv.org/abs/2010.05351)

    Paper: Identifying Melanoma Images using EfficientNet Ensemble:
    Winning Solution to the SIIM-ISIC Melanoma Classification Challenge

    Strategy
    --------
    1. Train-Val Set
    5-fold cross-validation on data from ISIC's 2018, 2019 and 2020 challenge. This leads to
    enormous class-imbalance, however they do no do any balancing. They also do not mention
    leakage between train and val set which must have occured but can probably be ignored.

    2. Target and metadata
    Even though the 2020 challenge was binary, they used a multiclass (n=9) approach. They
    also had some models which used metadata.

    3. Architectures
    They used a variety of architecture backbones (EfficientNet B3, B4, B5, B6, B7,
    SE-ResNeXt-101 and ResNeSt-101) and image sizes.

    4. Ensmeble
    They ensembled a total of 18 models. Each of these 18 models is itself an ensemble
    of 5 models which were obtained through 5-fold cross-validation.

    Model notes
    -----------
    EfficientNet-B0: 5.3M
    EfficientNet-B1: 7.8M
    EfficientNet-B2: 9.2M
    EfficientNet-B3: 12M
    EfficientNet-B4: 19M
    EfficientNet-B5: 30M
    EfficientNet-B6: 43M
    EfficientNet-B7: 66M
    SE-ResNeXt-101 : ??M
    ResNeSt-101    : 48M

    Class labels
    ------------
    Good to know for future classifications tasks aimed to be similar.
    For four classes: {'BKL': 0, 'melanoma': 1, 'nevus': 2, 'unknown': 3}
    For nine classes: {'AK': 0, 'BCC': 1, 'BKL': 2, 'DF': 3, 'SCC': 4,
                       'VASC': 5, 'melanoma': 6, 'nevus': 7, 'unknown': 8}

    seborrheic keratosis -> BKL
    lichenoid keratosis -> BKL
    solar lentigo -> BKL
    lentigo NOS -> BKL
    cafe-au-lait macule -> unknown
    atypical melanocytic proliferation -> unknown
    DF -> unknown
    AK -> unknown
    SCC -> unknown
    VASC -> unknown
    BCC -> unknown
    '''
    @staticmethod
    def get_transforms(img_size):
        '''Get transforms

        As they used models with different image sizes, image size is parameterized here.
        Their image sizes included 384, 448, 512, 576, 640, 768 and 896. Transforms were
        fixed across all architectures and image sizes.

        Parameters
        ----------
        img_size : int
            Size image will be resized to

        Returns
        -------
        A list of albumentation transforms.
        '''
        return [
            A.Transpose(p=0.5),
            A.VerticalFlip(p=0.5),
            A.HorizontalFlip(p=0.5),
            A.RandomBrightness(limit=0.2, p=0.75),
            A.RandomContrast(limit=0.2, p=0.75),
            A.OneOf([
                A.MotionBlur(blur_limit=5),
                A.MedianBlur(blur_limit=5),
                A.GaussianBlur(blur_limit=5),
                A.GaussNoise(var_limit=(5.0, 30.0)),
            ], p=0.7),
            A.OneOf([
                A.OpticalDistortion(distort_limit=1.0),
                A.GridDistortion(num_steps=5, distort_limit=1.),
                A.ElasticTransform(alpha=3),
            ], p=0.7),
            A.CLAHE(clip_limit=4.0, p=0.7),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=15, border_mode=0, p=0.85),
            A.Resize(img_size, img_size),
            A.Cutout(max_h_size=int(img_size * 0.375), max_w_size=int(img_size * 0.375), num_holes=1, p=0.7),
            A.Normalize(),
            ToTensorV2(),
        ]

    @staticmethod
    def get_criterion():
        '''Get loss function'''
        return F.cross_entropy

    @staticmethod
    def get_optimizer(params, lr=3e-4, epochs=15, warmup_epochs=1, discriminative_lr=False):
        '''Get optimizer(s) and scheduler(s).

        They used cosine annealing with one warm-up epoch and mostly 15 total epochs (except 18 once).
        Learning rated ranged from 1e-4 to 3e-4 and was tuned for every architecture. During warm-up,
        the learning rate is one thenth of the initial learning rate of the cosine cycle (i.e. lowest
        lr can be 3e-5 at warm-up). Batch size was 64 for all models.

        Note: learning rate was mostly 3e-4

        Parameters
        ----------
        params : iterable of torch Tensor
            Model's parameters

        lr : float; optinal
            Learning rate

        epochs : int; optional
            Number of training epochs

        warmup_epochs : int; optional
            Number of warmup epochs

        discriminative_lr : bool; optional
            If True, a discriminative lr is used and each layer/group in ´params´
            will have a different lr associated with it. Thus, the warmup lr for the
            linear warmup should also be discriminative which is however not possible.
            Therefore, the initial warmup lr is set to 0 instead of lr/10 which is
            the default in the paper.
        '''
        warmup_start_lr = lr/10 # default
        if discriminative_lr:
            warmup_start_lr = 0. # special case
        print(warmup_start_lr)
        optimizer = torch.optim.Adam(params, lr=lr)
        scheduler = LinearWarmupCosineAnnealingLR(
            optimizer=optimizer,
            warmup_epochs=warmup_epochs,
            max_epochs=epochs-1,
            warmup_start_lr=warmup_start_lr
        )

        return {"optimizer": optimizer, "lr_scheduler": scheduler}

class LasserProcedure():
    '''Lasser et al. ()

    Paper: FusionM4Net: A multi-stage multi-modal learning algorithm
    for multi-label skin lesion classification

    Notes
    -----
    They did their resize when loading images i.e. before applying tfms
    using cv2. They also wrapped their tfms in a ´A.Compose´ with an
    associated proba
    '''
    @staticmethod
    def get_transforms(img_size):
        '''Get transforms

        They did their resize when loading images i.e. before applying tfms
        using cv2. They also wrapped their tfms in a ´A.Compose´ with an
        associated probability of p=0.5
        '''
        return [
            A.Resize(img_size, img_size),
            A.VerticalFlip(p=0.5),
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.0625,scale_limit=0.5,rotate_limit=45,p=0.5),
            A.RandomRotate90(p=0.5),
            A.RandomBrightnessContrast(p=0.5),
            A.Normalize(),
            ToTensorV2(),
        ]

class ValleProcedure():
    '''Valle et al. (https://arxiv.org/abs/1809.01442)

    Paper: Data Augmentation for Skin Lesion Analysis
    '''
    @staticmethod
    def get_transforms(img_size):
        '''Get transforms'''
        return [
            A.Resize(img_size, img_size),
            A.Normalize(),
            ToTensorV2(),
        ]


class XuProcedure():
    '''Xu et al. (https://arxiv.org/ftp/arxiv/papers/2101/2101.02353)

    Paper: Low-cost and high-performance data augmentation for
    deep-learningbased skin lesion classification
    '''
    @staticmethod
    def get_transforms(img_size):
        '''Get transforms'''
        return [
            A.Resize(img_size, img_size),
            A.Normalize(),
            ToTensorV2(),
        ]

# Cell
def get_inference_tfms(img_size, normalize=True):
    '''Get basic albumentation transforms for inference'''
    tfms = [
            A.Resize(img_size, img_size),
            A.Normalize(),
            ToTensorV2(),
        ]

    if not normalize:
        tfms.pop(1)

    return tfms

def get_train_tfms(img_size, tfm_name):
    '''Get train transforms'''
    if tfm_name == "liu":
        return LiuProcedure.get_transforms(img_size)
    elif tfm_name == "lasser":
        return LasserProcedure.get_transforms(img_size)
    elif tfm_name == "valle":
        return ValleProcedure.get_transforms(img_size)
    elif tfm_name == "xu":
        return XuProcedure.get_transforms(img_size)
    elif tfm_name == "default":
        return get_inference_tfms(img_size)
    else:
        raise ValueError(f"Unknown transform name '{tfm_name}'")