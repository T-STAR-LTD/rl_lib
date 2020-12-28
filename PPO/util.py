import copy
import gym
import torch
import numpy as np
from collections import deque
from PPO import PPOClassical, PPOPixel
from Config import Config
import pdb
import wandb
from envs import make_env, VecPyTorch
from stable_baselines3.common.vec_env import DummyVecEnv

def train(config):
  env = copy.deepcopy(config.env)
  steps = 0
  scores_deque = deque(maxlen=100)
  scores = []
  average_scores = []
  max_score = -np.Inf

  agent = PPOClassical(config)
  
  if config.wandb:
    wandb.watch(agent.model)

  for i_episode in range(1, config.n_episodes+1):
    state = env.reset()
    score = 0
    for t in range(config.max_t):
      steps += 1

      action, log_prob, values, _ = agent.act(torch.FloatTensor(state))
      next_state, reward, done, _ = env.step(action.item())

      agent.add_to_mem(state, action, reward, log_prob, values, done)

      # Update 
      state = next_state
      score += reward

      if steps >= config.update_every:
        agent.learn(config.num_learn)
        agent.mem.clear()
        steps = 0

      if done:
        break 

    # Book Keeping
    scores_deque.append(score)
    scores.append(score)
    average_scores.append(np.mean(scores_deque))

    if i_episode % 10 == 0:
      print("\rEpisode {}	Average Score: {:.2f}	Score: {:.2f}".format(i_episode, np.mean(scores_deque), score), end="")
    if i_episode % 100 == 0:
      print("\rEpisode {}	Average Score: {:.2f}".format(i_episode, np.mean(scores_deque)))   

    if np.mean(scores_deque) > config.win_condition:
      print("\nEnvironment Solved!")
      break

  return scores, average_scores

def train_pixel(config):
  # env = config.env
  envs = VecPyTorch(DummyVecEnv([make_env(config.env_id, config.seed+i, i) for i in range(config.num_env)]), config.device)
  scores_deque = deque(maxlen=100)
  scores = []
  average_scores = []
  global_step = 0

  agent = PPOPixel(config)

  if config.wandb:
    wandb.watch(agent.model)

  while global_step < config.n_steps:
    states = envs.reset()
    score = 0
    values, dones = None, None
    
    while agent.mem.isFull() == False:
      global_step += config.num_env

      # Take actions
      # with torch.no_grad():
      actions, log_probs, values, entrs = agent.act(states)
      next_states, rewards, dones, infos = envs.step(actions)

      # Add to memory buffer
      agent.add_to_mem(states, actions, rewards, log_probs, values, dones)
      # Update state
      states = next_states

      
      # Book Keeping
      for info in infos:
        if 'episode' in info:
          score = info['episode']['r']
          config.tb_logger.add_scalar("charts/episode_reward", score, global_step)
          if config.wandb:
            wandb.log({
              "episode_reward": score,
              "global_step": global_step
            })
          
          scores_deque.append(score)
          scores.append(score)
          average_scores.append(np.mean(scores_deque))

    # update and learn
    value_loss, pg_loss, approx_kl, approx_entropy, lr_now = agent.learn(config.num_learn, values, dones, global_step)
    agent.mem.reset()

    # Book Keeping
    config.tb_logger.add_scalar("losses/value_loss", value_loss.item(), global_step)
    config.tb_logger.add_scalar("losses/policy_loss", pg_loss.item(), global_step)
    config.tb_logger.add_scalar("losses/approx_kl", approx_kl.item(), global_step)
    config.tb_logger.add_scalar("losses/approx_entropy", approx_entropy.item(), global_step)

    if config.wandb:
      wandb.log({
        "value_loss": value_loss,
        "policy_loss": pg_loss,
        "approx_kl": approx_kl,
        "approx_entropy": approx_entropy,
        "global_step": global_step,
        "learning_rate": lr_now
       })

    print("Global Step: {}	Average Score: {:.2f}".format(global_step, np.mean(scores_deque)))   

  return scores, average_scores
