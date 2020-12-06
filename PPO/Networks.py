import torch.nn as nn
import numpy as np
import torch
from Config import Config
import pdb

# TODO:
# - Layer initialisation

class cnn_head_model(nn.Module):
  def __init__(self, config):
    # Call inheritance
    super(cnn_head_model, self).__init__()
    self.config = config
    self.head = nn.Sequential(
      nn.Conv2d(4, 32, kernel_size=8, stride=4),
      # nn.BatchNorm2d(32),
      nn.ReLU(),
      nn.Conv2d(32, 64, kernel_size=4, stride=2),
      # nn.BatchNorm2d(64),
      nn.ReLU(),
      nn.Conv2d(64, 64, kernel_size=3, stride=1),
      # nn.BatchNorm2d(64),
      nn.ReLU(),
      nn.Flatten(),
      nn.Linear(64 * 7 * 7, self.config.hidden_size),
      nn.ReLU(),
    )

  def forward(self, state):
    return self.head(state)

def head_model(config: Config) -> nn.Sequential:
  return nn.Sequential(
    nn.Linear(config.state_space, config.hidden_size),
    nn.ReLU()
  )

def actor_model(config: Config) -> nn.Sequential:
  return nn.Sequential(
    nn.Linear(config.hidden_size, config.hidden_size),
    nn.ReLU()
  )

def critic_model(config: Config) -> nn.Sequential:
  return nn.Sequential(
    nn.Linear(config.hidden_size, config.hidden_size),
    nn.ReLU()
  )
