from memory_env import MemoryEnv
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback, BaseCallback
import json
import os
import numpy as np

TOTAL_TIMESTEPS = 200000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, "..", "..", "models", "rl_models", "ppo_ramwise")
LOG_PATH = os.path.join(SCRIPT_DIR, "..", "..", "models", "rl_models", "rl_training_log.json")
BEST_MODEL_DIR = os.path.join(SCRIPT_DIR, "..", "..", "models", "rl_models")
EVAL_FREQ = 5000


class RewardLoggerCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []

    def _on_step(self):
        return True

    def _on_rollout_end(self):
        if self.locals.get("infos"):
            for info in self.locals["infos"]:
                if "episode" in info:
                    self.episode_rewards.append(info["episode"]["r"])


if __name__ == "__main__":
    os.makedirs(BEST_MODEL_DIR, exist_ok=True)
    print("Initializing RAMWise RL Training...")

    env = make_vec_env(MemoryEnv, n_envs=1)
    eval_env = make_vec_env(MemoryEnv, n_envs=1)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=0.0003,
        n_steps=512,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        device="cpu",
    )

    reward_logger = RewardLoggerCallback(verbose=0)
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=BEST_MODEL_DIR + os.sep,
        log_path=BEST_MODEL_DIR + os.sep,
        eval_freq=EVAL_FREQ,
        deterministic=True,
        render=False,
    )

    print("Starting PPO training for 50000 timesteps...")
    model.learn(total_timesteps=TOTAL_TIMESTEPS, callback=[reward_logger, eval_callback])
    model.save(MODEL_SAVE_PATH)
    print("Model saved to models/rl_models/ppo_ramwise.zip")

    obs = eval_env.reset()
    total_reward = 0.0
    for _ in range(200):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, info = eval_env.step(action)
        total_reward += reward[0]
        if done[0]:
            obs = eval_env.reset()
    avg_episode_reward = total_reward / 200.0

    training_log = {
        "total_timesteps": 50000,
        "avg_episode_reward": float(avg_episode_reward),
        "episode_rewards_sample": reward_logger.episode_rewards[-10:] if reward_logger.episode_rewards else [],
        "model_path": "models/rl_models/ppo_ramwise.zip",
        "status": "completed",
    }
    with open(LOG_PATH, "w") as f:
        json.dump(training_log, f, indent=2)

    print("RL Training complete.")
    print(f"Average episode reward: {avg_episode_reward:.2f}")
