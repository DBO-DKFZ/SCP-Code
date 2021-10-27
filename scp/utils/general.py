# AUTOGENERATED! DO NOT EDIT! File to edit: nb_utils.general.ipynb (unless otherwise specified).

__all__ = ['load_config_yaml', 'p2t', 't2p', 'a2p', 'AggregatingHook', 'n_argmin', 'n_argmax', 'state_dicts_equal',
           'convert_state_dict', 'custom_save', 'custom_load']

# Cell
import yaml
import os
import torchvision
import PIL
from pathlib import Path
from fastai.vision.all import *
import gc
import torch

# Cell
def load_config_yaml(path_to_yaml):
    '''Load project config yaml and change relative paths to absolute paths'''

    with open(path_to_yaml) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    parent_dir = Path(os.path.dirname(os.getcwd()))
    for k, v in config.items():
        if "path" in k:
            config[k] = parent_dir/v
    return config

# Cell
p2t = torchvision.transforms.ToTensor()
t2p = torchvision.transforms.ToPILImage()
a2p = PIL.Image.fromarray

# Cell
class AggregatingHook(Hook):
    '''aggregate hook outputs in 'stored' in case inference is carried out over the entire dataset in a loop'''
    def __init__(self, m, hook_func, is_forward=True, detach=True, cpu=False, gather=False):
        super().__init__(m, hook_func, is_forward, detach, cpu, gather)
        self.stored = list()

    def hook_fn(self, module, input, output):
        "Applies `hook_func` to `module`, `input`, `output`."
        if self.detach:
            input,output = to_detach(input, cpu=self.cpu, gather=self.gather),to_detach(output, cpu=self.cpu, gather=self.gather)
        self.stored.append(self.hook_func(module, input, output))


# Cell
def n_argmin(arr:np.array, n:int):
    '''returns the indices of the n-smallest values. Note that these may not be in sorted order!'''
    return np.argpartition(arr, n)[:, :n]

def n_argmax(arr:np.array, n:int):
    '''returns the indices of the n-largest  values. Note that these may not be in sorted order!'''
    return np.argpartition(arr, -n)[:, -n:]

# Cell
def state_dicts_equal(state_dict1:dict, state_dict2:dict, verbose:bool=False):
    '''Check if two state dicts are the same with a margin of error

    Do not need to have the same key names but need same number of keys
    '''

    equal = True

    # check if state dicts have same length
    if len(state_dict1) != len(state_dict2):
        equal = False
        error_msg = f"Length mismatch of {len(state_dict1)} and {len(state_dict2)}"

    # check if state dicts have same shape and content
    for (k1, v1), (k2, v2) in zip(state_dict1.items(), state_dict2.items()):
        if not torch.allclose(v1, v2):
            equal = False
            if v1.shape != v2.shape:
                error_msg = f"Shape mismatch for keys '{k1}' ({v1.shape}) and '{k2}' ({v2.shape})"
            else:
                error_msg = f"Content mismatch for keys '{k1}' and '{k2}'"

    # show errors if applicable
    if verbose and not equal:
        print(error_msg)

    return equal

def convert_state_dict(state_dict1:dict, state_dict2:dict, strict:bool=True, verbose:bool=False):
    '''Using keys from 1 and values from 2

    Will return a state dict that has min number of keys min(state_dict1, state_dict2).
    '''

    state_dict = OrderedDict()
    count = 0

    for (k1, v1), (k2, v2) in zip(state_dict1.items(), state_dict2.items()):

        # if strict is True we only want layers that match each other's shape
        if strict:
            if v1.shape==v2.shape:
                state_dict[k1] = v2
            else:
                count += 1
        # if strict is False we simply fuse the keys and values from dict1 and dict2 respectively
        else:
            state_dict[k1] = v2

    if verbose:
        print(f"New state dict has  {len(state_dict)} layers based on previous {len(state_dict1)} and {len(state_dict2)} layers")
        if strict:
            print(f"Ignored {count} layers due to shape mismatch")
    return state_dict

# Cell
def custom_save(obj, path, final_run:bool=False):

    tag = ""
    if final_run:
        tag = "_final"

    torch.save(obj, f"{path}{tag}.pkl")

def custom_load(path, final_run:bool=False):

    tag = ""
    if final_run:
        tag = "_final"

    return torch.load(f"{path}{tag}.pkl")