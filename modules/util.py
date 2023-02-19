#!/usr/bin/env python3
# Author: Armit
# Create Time: 2022/09/15 

import os
import sys
import random
from pathlib import Path
from datetime import datetime
import pickle as pkl
import logging

import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import precision_recall_fscore_support

from modules.typing import *

plt.rcParams['font.sans-serif'] = ['SimHei']    # 显示中文
plt.rcParams['axes.unicode_minus'] = False      # 正常显示负号

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging


def get_logger(name, base_path=Path('log')):
  global logger
  logger = logging.getLogger(name)
  logger.setLevel(logging.DEBUG)
  
  formatter = logging.Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s")
  h = logging.FileHandler(base_path / name / 'log.log')
  h.setLevel(logging.DEBUG)
  h.setFormatter(formatter)
  logger.addHandler(h)
  return logger


def seed_everything(seed:int):
  random.seed(seed)
  os.environ["PYTHONHASHSEED"] = str(seed)
  np.random.seed(seed)
  torch.manual_seed(seed)
  torch.cuda.manual_seed_all(seed)
  torch.backends.cudnn.deterministic = True
  torch.backends.cudnn.benchmark = False

def timestr():
  return f'{datetime.now()}'.replace(' ', 'T').replace(':', '-').split('.')[0]


def save_metrics(truth, pred, fp:Path, task:ModelTask='clf'):
  assert task in ['clf', 'rgr'], ValueError(f'unknown task {task!r}')

  with open(fp, 'w', encoding='utf-8') as fh:
    def log(s:str):
      fh.write(f'{s}\n')
      print(s)

    if task == 'clf':
      prec, recall, f1, supp = precision_recall_fscore_support(truth, pred)
      log(f'prec:   {prec:.3%}')
      log(f'recall: {recall:.3%}')
      log(f'f1:     {f1:.3%}')
    elif task == 'rgr':
      mae = mean_absolute_error(truth, pred)
      mse = mean_squared_error(truth, pred)
      r2  = r2_score(truth, pred)
      log(f'mae: {mae:.3f}')
      log(f'mse: {mse:.3f}')
      log(f'r2:  {r2:.3f}')

def save_figure(fp:Path, title:str=None):
  plt.tight_layout()
  plt.suptitle(title)
  plt.savefig(fp, dpi=400)
  print(f'  save figure to {fp}')


def load_pickle(fp:Path) -> CachedData:
  if not fp.exists(): return
  print(f'  load pickle from {fp}')
  with open(fp, 'rb') as fh:
    return pkl.load(fh)

def save_pickle(data:CachedData, fp:Path):
  print(f'  save pickle to {fp}')
  with open(fp, 'wb') as fh:
    pkl.dump(data, fh)


def load_checkpoint(checkpoint_path, model, optimizer=None):
  checkpoint_dict = torch.load(checkpoint_path, map_location='cpu')
  iteration = checkpoint_dict['iteration']
  learning_rate = checkpoint_dict['learning_rate']
  if optimizer is not None:
    optimizer.load_state_dict(checkpoint_dict['optimizer'])
  state_dict = checkpoint_dict['model']
  new_state_dict= {}
  for k, v in model.state_dict().items():
    try:
      new_state_dict[k] = state_dict[k]
    except:
      logger.info("%s is not in the checkpoint" % k)
      new_state_dict[k] = v
  model.load_state_dict(new_state_dict)
  logger.info(f"Loaded checkpoint '{checkpoint_path}' (iteration {iteration})")
  return model, optimizer, learning_rate, iteration

def save_checkpoint(model, optimizer, learning_rate, iteration, checkpoint_path):
  logger.info(f"Saving model and optimizer state at iteration {iteration} to {checkpoint_path}")
  state_dict = model.state_dict()
  torch.save({'model': state_dict,
              'iteration': iteration,
              'optimizer': optimizer.state_dict(),
              'learning_rate': learning_rate}, checkpoint_path)


def plot_predict(ys:list, y_hats:list, save_fp:str='predict.png'):
  n_figs = len(ys)
  fig = plt.figure(figsize=(12,8))
  lst=['COD','TN','NH3-N','TP','PH']  #注意根据因子修改
  a=0
  for i, (y, y_hat) in enumerate(zip(ys, y_hats), start=1):
    plt.subplot(n_figs, 1, i)
    plt.plot(y_hat, 'r',label='forcast')
    plt.plot(y, 'b',label='true')
    plt.ylabel(lst[a])
    a+=1
    if a==1:
        legend = plt.legend(ncol=2,loc='best')
  fig.tight_layout(pad=0.5, w_pad=0, h_pad=0)
  print(f'[plot_predict] save to {save_fp}')
  plt.savefig(save_fp,dpi=500)

  plt.show()
