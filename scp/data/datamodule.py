# AUTOGENERATED! DO NOT EDIT! File to edit: nb_data.datamodule.ipynb (unless otherwise specified).

__all__ = ['MultiLabelDataFrameDataModule', 'DataFrameDataModule']

# Cell
from torch.utils.data import DataLoader
from torchsampler import ImbalancedDatasetSampler
from pytorch_lightning import LightningDataModule
from .dataset import DataFrameImageDataset, MultiLabelDataFrameImageDataset
import pandas as pd

class MultiLabelDataFrameDataModule(LightningDataModule):
    '''Data module where the underlying dataset is a ´DataFrameImageDataset´.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing image paths, corresponding labels (optional) and
        what set the image belongs to (i.e. train, val, test, predict).

    img_col : str
        Name of df column containing image paths

    set_col : str
        Name of df column containing set designation.
        Column must contain one or more of ´train´, ´val´, ´test´ or ´predict´.

    label_col : str; optional
        Name of df column containing image labels.
        If None, ´self.label_col´ are all zeros.

    root : str; optional
        Top-level directory that gets prepended to image paths

    transforms : dict; optional
        Dict of composition of albumentation transforms (or any transforms that work on numpy arrays).
        Dict keys must be one or more of ´train´, ´val´, ´test´ or ´predict´.

    label_names : list; optional
        List of unique label names. Order of list determines what integer a label is mapped to.
        If None, ´self.label_names´ are determined by ´self.label´.

    batch_size : int; optional
        Batch size at loading.

    num_workers : int; optional
        Number of cpu cores.

    balance_train_ds : bool, optional
        If True, the train dataloader samples balanced batches.
    '''
    def __init__(
        self,
        df,
        img_col,
        set_col,
        label_cols,
        root="./",
        transforms=dict(),
        label_class_names=None,
        batch_size=32,
        num_workers=1,
        balance_train_ds=False
    ):
        super().__init__()
        self.df = df
        self.img_col = img_col
        self.set_col = set_col
        self.label_cols = label_cols
        self.root = root
        self.transforms = transforms
        self.label_class_names = label_class_names
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.balance_train_ds = balance_train_ds

        self.setup_called = False

    def setup(self, stage=None, ):

        if self.setup_called:
            print("Setup has already been called. Set attribute 'setup_called=False' if you want to explicitly reset this.")
        else:
            self.setup_called = True
            self._train_dss, self.train_dss_names = self._get_datasets(set_name="train")
            self._val_dss, self.val_dss_names = self._get_datasets(set_name="val")
            self._test_dss, self.test_dss_names = self._get_datasets(set_name="test")
            self._predict_dss, self.predict_dss_names = self._get_datasets(set_name="predict")

    def train_dataloader(self, idx=0):
        sampler, shuffle = None, True
        if self.balance_train_ds:
            sampler, shuffle = ImbalancedDatasetSampler, False
        dls = self._get_dataloaders(self._train_dss, sampler, shuffle)
        if idx != None:
            return dls[idx]
        return dls

    def val_dataloader(self, idx=None):
        sampler, shuffle = None, False
        dls = self._get_dataloaders(self._val_dss, sampler, shuffle)
        if idx != None:
            return dls[idx]
        return dls

    def test_dataloader(self, idx=None):
        sampler, shuffle = None, False
        dls = self._get_dataloaders(self._test_dss, sampler, shuffle)
        if idx != None:
            return dls[idx]
        return dls

    def predict_dataloader(self, idx=None):
        sampler, shuffle = None, False
        dls = self._get_dataloaders(self._predict_dss, sampler, shuffle)
        if idx != None:
            return dls[idx]
        return dls

    def train_dataset(self, idx=0):
        if idx != None:
            return self._train_dss[idx]
        return self._train_dss

    def val_dataset(self, idx=None):
        if idx != None:
            return self._val_dss[idx]
        return self._val_dss

    def test_dataset(self, idx=None):
        if idx != None:
            return self._test_dss[idx]
        return self._test_dss

    def predict_dataset(self, idx=None):
        if idx != None:
            return self._predict_dss[idx]
        return self._predict_dss

    def _get_dataloaders(self, dss, sampler, shuffle):
        dls = list()
        for ds in dss:

            sampler_instance = None
            if sampler:
                sampler_instance = sampler(ds)

            dls.append(DataLoader(
                dataset=ds,
                batch_size=self.batch_size,
                num_workers=self.num_workers,
                sampler=sampler_instance,
                shuffle=shuffle
            ))

        return dls

    def _get_datasets(self, set_name):
        '''Get dataset(s) for a particular set.

        Parameters
        ----------
        set_name : str
            Should be one of ´train´, ´val´, ´test´ or ´predict´

        Returns
        -------
        List with at least one ´DataFrameImageDataset´ (which could be empty)
        '''

        set_df = self.df[self.df[self.set_col].str.contains(set_name)]

        # get subset dataframe(s) for this particular set
        subset_names = list()
        subset_dfs = list()
        for subset_name, subset_df in set_df.groupby(self.set_col, sort=True):
            subset_names.append(subset_name)
            subset_dfs.append(subset_df.reset_index(drop=True))

        # in case no subsets where found, add empty df for compatibility
        if len(subset_dfs)==0:
            subset_names.append(set_name)
            subset_dfs.append(pd.DataFrame(columns=set_df.columns))

        # create dataset(s) for this particular set
        subset_dss = list()
        for subset_df in subset_dfs:
            subset_dss.append(MultiLabelDataFrameImageDataset(
                df=subset_df,
                img_col=self.img_col,
                label_cols=self.label_cols,
                root=self.root,
                img_transform=self.transforms.get(set_name),
                label_class_names=self.label_class_names,
            ))

        return subset_dss, subset_names

    def update_ds_tfms(self, set_name, idx, tfms):
        if set_name=="train":
            self._train_dss[idx].img_transform = tfms
        elif set_name=="val":
            self._val_dss[idx].img_transform = tfms
        elif set_name=="test":
            self._test_dss[idx].img_transform = tfms
        elif set_name=="predict":
            self._predict_dss[idx].img_transform = tfms
        else:
            raise ValueError(f"Unknown set name {set_name}")

class DataFrameDataModule(LightningDataModule):
    '''Data module where the underlying dataset is a ´DataFrameImageDataset´.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing image paths, corresponding labels (optional) and
        what set the image belongs to (i.e. train, val, test, predict).

    img_col : str
        Name of df column containing image paths

    set_col : str
        Name of df column containing set designation.
        Column must contain one or more of ´train´, ´val´, ´test´ or ´predict´.

    label_col : str; optional
        Name of df column containing image labels.
        If None, ´self.label_col´ are all zeros.

    root : str; optional
        Top-level directory that gets prepended to image paths

    transforms : dict; optional
        Dict of composition of albumentation transforms (or any transforms that work on numpy arrays).
        Dict keys must be one or more of ´train´, ´val´, ´test´ or ´predict´.

    label_names : list; optional
        List of unique label names. Order of list determines what integer a label is mapped to.
        If None, ´self.label_names´ are determined by ´self.label´.

    batch_size : int; optional
        Batch size at loading.

    num_workers : int; optional
        Number of cpu cores.

    balance_train_ds : bool, optional
        If True, the train dataloader samples balanced batches.
    '''
    def __init__(
        self,
        df,
        img_col,
        set_col,
        label_col=None,
        root="./",
        transforms=dict(),
        label_names=None,
        batch_size=16,
        num_workers=1,
        balance_train_ds=False
    ):
        super().__init__()
        self.df = df
        self.img_col = img_col
        self.set_col = set_col
        self.label_col = label_col
        self.root = root
        self.transforms = transforms
        self.label_names = label_names
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.balance_train_ds = balance_train_ds
        #self.setup()

    def setup(self, stage=None):
        self.train_dss = self._get_datasets(set_name="train")
        self.val_dss = self._get_datasets(set_name="val")
        self.test_dss = self._get_datasets(set_name="test")
        self.predict_dss = self._get_datasets(set_name="predict")

    def train_dataloader(self):
        sampler, shuffle = None, True
        if self.balance_train_ds:
            sampler, shuffle = ImbalancedDatasetSampler, False
        return self._get_dataloaders(self.train_dss, sampler, shuffle)[0] # DO not want to implement multiple dl trainging

    def val_dataloader(self):
        sampler, shuffle = None, False
        return self._get_dataloaders(self.val_dss, sampler, shuffle)

    def test_dataloader(self):
        sampler, shuffle = None, False
        return self._get_dataloaders(self.test_dss, sampler, shuffle)[0]

    def predict_dataloader(self):
        sampler, shuffle = None, False
        return self._get_dataloaders(self.predict_dss, sampler, shuffle)[0]

    def _get_dataloaders(self, dss, sampler, shuffle):
        dls = list()
        for ds in dss:

            sampler_instance = None
            if sampler:
                sampler_instance = sampler(ds)

            dls.append(DataLoader(
                dataset=ds,
                batch_size=self.batch_size,
                num_workers=self.num_workers,
                sampler=sampler_instance,
                shuffle=shuffle
            ))

        return dls

    def _get_datasets(self, set_name):
        '''Get dataset(s) for a particular set.

        Parameters
        ----------
        set_name : str
            Should be one of ´train´, ´val´, ´test´ or ´predict´

        Returns
        -------
        List with at least one ´DataFrameImageDataset´ (which could be empty)
        '''

        set_df = self.df[self.df[self.set_col].str.contains(set_name)]

        # get subset dataframe(s) for this particular set
        subset_dfs = list()
        for _, subset_df in set_df.groupby(self.set_col, sort=True):
            subset_dfs.append(subset_df.reset_index(drop=True))

        # in case no subsets where found, add empty df for compatibility
        if len(subset_dfs)==0:
            subset_dfs.append(pd.DataFrame(columns=set_df.columns))

        # create dataset(s) for this particular set
        subset_dss = list()
        for subset_df in subset_dfs:
            subset_dss.append(DataFrameImageDataset(
                df=subset_df,
                img_col=self.img_col,
                label_col=self.label_col,
                root=self.root,
                img_transform=self.transforms.get(set_name),
                label_names=self.label_names,
            ))

        return subset_dss