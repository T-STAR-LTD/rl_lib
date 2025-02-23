import numpy as np
import torch 
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from Networks import layer_init
import pdb 

class Scale(nn.Module):
  def __init__(self, scale):
    super().__init__()
    self.scale = scale

  def forward(self, x):
    return x * self.scale


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
  torch.nn.init.orthogonal_(layer.weight, std)
  torch.nn.init.constant_(layer.bias, bias_const)
  return layer

class ActorCriticModular(nn.Module):
  """Some Information about ActorCritic"""
  def __init__(self, config):
    super(ActorCritic, self).__init__()

    self.head = config.head_model()

    self.actor = config.actor_model()
    self.actor.add_module(
      "actor_linear",
      layer_init(nn.Linear(config.hidden_size, config.action_space))
    )

    self.critic = config.critic_model()
    self.critic.add_module(
      "critic_linear",
      layer_init(nn.Linear(config.hidden_size, 1))
    )

  def forward(self, x):
    x = self.head(x)
    value = self.critic(x)
    action = self.actor(x)
    return action, value
  
  def act(self, x, action=None):
    logits, value = self.forward(x)
    probs = Categorical(logits=logits)
    if action is None:
      action = probs.sample()
    return action, probs.log_prob(action), value, probs.entropy()

class ActorCritic(nn.Module):
  def __init__(self, config):
    super(ActorCritic, self).__init__()
    self.network = nn.Sequential(
      layer_init(nn.Linear(config.state_space, config.hidden_size), std=0.01),
      nn.ReLU(),
      layer_init(nn.Linear(config.hidden_size, config.hidden_size), std=0.01),
      nn.ReLU()
    )
    self.actor = layer_init(nn.Linear(config.hidden_size, config.action_space), std=0.01)
    self.critic = layer_init(nn.Linear(config.hidden_size, 1), std=1)

  def forward(self, x):
    return self.network(x)

  def act(self, x, action=None):
    values = self.critic(self.forward(x))
    logits = self.actor(self.forward(x))
    probs = Categorical(logits=logits)
    if action is None:
      action = probs.sample()
    return action, probs.log_prob(action), values, probs.entropy()
  
  def get_values(self, x):
    return self.critic(self.forward(x))


class ActorCriticCnn(nn.Module):
  def __init__(self, config):
    super(ActorCriticCnn, self).__init__()
    channels = 3
    self.network = nn.Sequential(
      Scale(1/255),
      layer_init(nn.Conv2d(4, 32, 8, stride=4)),
      nn.ReLU(),
      layer_init(nn.Conv2d(32, 64, 4, stride=2)),
      nn.ReLU(),
      layer_init(nn.Conv2d(64, 64, 3, stride=1)),
      nn.ReLU(),
      nn.Flatten(),
      layer_init(nn.Linear(3136, config.hidden_size)),
      nn.ReLU()
    )
    self.actor = layer_init(nn.Linear(config.hidden_size, config.action_space), std=0.01)
    self.critic = layer_init(nn.Linear(config.hidden_size, 1), std=1)

  def forward(self, x):
    return self.network(x)

  def act(self, x, action=None):
    # pdb.set_trace()
    values = self.critic(self.forward(x))
    logits = self.actor(self.forward(x))
    probs = Categorical(logits=logits)
    if action is None:
      action = probs.sample()
    return action, probs.log_prob(action), values, probs.entropy()
  
  def get_values(self, x):
    return self.critic(self.forward(x))



class ActorCriticCnnProcGen(nn.Module):
  def __init__(self, config):
    super(ActorCriticCnnProcGen, self).__init__()
    channels = 3
    self.network = nn.Sequential(
      Scale(1/255),
      layer_init(nn.Conv2d(channels, 32, 4, stride=3)),
      nn.ReLU(),
      layer_init(nn.Conv2d(32, 64, 3, stride=2)),
      nn.ReLU(),
      layer_init(nn.Conv2d(64, 32, 3, stride=1)),
      nn.ReLU(),
      nn.Flatten(),
      layer_init(nn.Linear(8*8*32, config.hidden_size)),
      nn.ReLU()
    )
    self.actor = layer_init(nn.Linear(config.hidden_size, config.action_space), std=0.01)
    self.critic = layer_init(nn.Linear(config.hidden_size, 1), std=1)

  def forward(self, x):
    return self.network(x.permute((0, 3, 1, 2))) # "bhwc" -> "bchw"

  def act(self, x, action=None):
    values = self.critic(self.forward(x))
    logits = self.actor(self.forward(x))
    probs = Categorical(logits=logits)
    if action is None:
      action = probs.sample()
    return action, probs.log_prob(action), values, probs.entropy()
  
  def get_values(self, x):
    return self.critic(self.forward(x))

