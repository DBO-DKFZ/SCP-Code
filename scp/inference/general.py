# AUTOGENERATED! DO NOT EDIT! File to edit: nb_inference.general.ipynb (unless otherwise specified).

__all__ = ['convert_test_df']

# Cell
import pandas as pd
import numpy as np

# Cell
def convert_test_df(df):
    '''Converts a df designed for testing to a train/val df as this easier to use for fastai batch inference'''
    dummy_train = df.copy()
    val = df.copy()

    dummy_train["is_valid"] = False
    val["is_valid"] = True

    return val.append(dummy_train, ignore_index=True)