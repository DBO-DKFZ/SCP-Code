# AUTOGENERATED! DO NOT EDIT! File to edit: nb_inference.general.ipynb (unless otherwise specified).

__all__ = ['convert_test_df', 'PredictionWriter']

# Cell
import pandas as pd
import numpy as np
from pytorch_lightning.callbacks import BasePredictionWriter
import torch
import os
from pathlib import Path

# Cell
def convert_test_df(df):
    '''Converts a df designed for testing to a train/val df as this easier to use for fastai batch inference'''
    dummy_train = df.copy()
    val = df.copy()

    dummy_train["is_valid"] = False
    val["is_valid"] = True

    return val.append(dummy_train, ignore_index=True)

# Cell
class PredictionWriter(BasePredictionWriter):
    '''Blabla

    Parameters
    ----------

    splits : dict; optional
        Contains
    '''
    def __init__(self, output_dir:str, output_file:str, dataset_names=list(), write_interval="epoch"):
        super().__init__(write_interval)
        self.output_dir = output_dir
        self.output_file = output_file
        self.dataset_names = dataset_names
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def write_on_epoch_end(self, trainer, pl_module, predictions, batch_indices):

        dataset_names = self.dataset_names
        if len(dataset_names)==0:
            dataset_names = np.arange(len(predictions))

        preds = dict()
        for dataset_name, prediction in zip(dataset_names, predictions):
            probs, gts = zip(*prediction)
            probs, gts = torch.concat(probs, dim=0), torch.concat(gts, dim=0)
            preds[dataset_name] = (probs, gts)

        torch.save(preds, os.path.join(self.output_dir, f"{self.output_file}.pt"))