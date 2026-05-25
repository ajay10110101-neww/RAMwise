import gymnasium as gym
from gymnasium.spaces import Box, Discrete
import numpy as np
import random
import json
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ramwise_combined_dataset.json")

class MemoryEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.num_apps = 150
        self.cache_size = 10
        self.action_meanings = {
            0: "preload_app",
            1: "evict_app",
            2: "move_to_hot",
            3: "move_to_warm",
            4: "move_to_cold",
        }
        self.action_space = Discrete(5)
        self.observation_space = Box(
            low=np.zeros(10, dtype=np.float32),
            high=np.ones(10, dtype=np.float32),
            dtype=np.float32,
        )
        self.max_steps = 200
        with open(DATASET_PATH, "r") as f:
            self.dataset = json.load(f)
        self.dataset_len = len(self.dataset)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.ram_usage = random.uniform(0.4, 0.9)
        self.battery_level = random.uniform(0.2, 1.0)
        self.cpu_usage = random.uniform(0.1, 0.8)
        all_apps = list(range(self.num_apps))
        random.shuffle(all_apps)
        self.hot_apps = set(all_apps[:3])
        self.warm_apps = set(all_apps[3:8])
        self.cold_apps = set(all_apps[8:])
        self.current_step = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.thrashing_count = 0
        self.dataset_idx = random.randint(0, self.dataset_len - self.max_steps - 1)
        record = self.dataset[self.dataset_idx]
        self.predicted_app = record["target_app"]
        self.current_hour = record["hour_normalized"]
        return self._get_obs(), {}

    def _get_obs(self):
        cache_hit_rate = self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        num_hot = len(self.hot_apps)
        num_warm = len(self.warm_apps)
        num_cold = len(self.cold_apps)
        return np.array(
            [
                self.ram_usage,
                self.battery_level,
                self.cpu_usage,
                min(num_hot / self.cache_size, 1.0),
                min(num_warm / self.num_apps, 1.0),
                min(num_cold / self.num_apps, 1.0),
                self.predicted_app / self.num_apps,
                cache_hit_rate,
                min(self.thrashing_count / 100.0, 1.0),
                self.current_hour,
            ],
            dtype=np.float32,
        )

    def step(self, action):
        self.current_step += 1
        reward = 0.0
        self.dataset_idx += 1
        if self.dataset_idx >= self.dataset_len:
            self.dataset_idx = 0
        record = self.dataset[self.dataset_idx]
        launched_app = record["target_app"]
        self.current_hour = record["hour_normalized"]

        if launched_app in self.hot_apps:
            self.cache_hits += 1
            reward += 1.0
        elif launched_app in self.warm_apps:
            self.cache_hits += 1
            reward += 0.3
        else:
            self.cache_misses += 1
            reward -= 0.5

        if action == 0:
            if self.ram_usage > 0.8:
                reward -= 0.5
            elif self.battery_level < 0.3:
                reward -= 0.4
            elif len(self.hot_apps) >= self.cache_size:
                reward -= 0.3
            elif self.ram_usage < 0.6 and self.battery_level > 0.4:
                self.hot_apps.add(self.predicted_app)
                self.warm_apps.discard(self.predicted_app)
                self.cold_apps.discard(self.predicted_app)
                reward += 0.6
            else:
                reward -= 0.2
        elif action == 1:
            if self.ram_usage < 0.5:
                reward -= 0.5
            elif len(self.hot_apps) > 0 and self.ram_usage > 0.7:
                evicted = random.choice(list(self.hot_apps))
                self.hot_apps.remove(evicted)
                self.cold_apps.add(evicted)
                self.thrashing_count += 1
                reward += 0.4
            else:
                reward -= 0.2
        elif action == 2:
            if self.ram_usage > 0.8:
                reward -= 0.3
            elif len(self.warm_apps) > 0 and len(self.hot_apps) < self.cache_size:
                app = random.choice(list(self.warm_apps))
                self.warm_apps.remove(app)
                self.hot_apps.add(app)
                reward += 0.3 if self.ram_usage < 0.65 else 0.1
            else:
                reward -= 0.1
        elif action == 3:
            if self.ram_usage > 0.85:
                reward -= 0.3
            elif len(self.cold_apps) > 0 and len(self.warm_apps) < 20:
                app = random.choice(list(self.cold_apps))
                self.cold_apps.remove(app)
                self.warm_apps.add(app)
                reward += 0.15 if self.ram_usage < 0.7 else -0.1
            else:
                reward -= 0.2
        elif action == 4:
            if self.ram_usage < 0.5:
                reward -= 0.5
            elif len(self.hot_apps) > 0 and self.ram_usage > 0.65:
                app = random.choice(list(self.hot_apps))
                self.hot_apps.remove(app)
                self.cold_apps.add(app)
                reward += 0.5 if self.ram_usage > 0.8 else 0.2
            else:
                reward -= 0.2

        self.ram_usage = max(0.1, min(1.0, self.ram_usage + random.uniform(-0.05, 0.05)))
        self.battery_level = max(0.0, min(1.0, self.battery_level - random.uniform(0.001, 0.005)))
        self.cpu_usage = max(0.05, min(1.0, self.cpu_usage + random.uniform(-0.1, 0.1)))
        next_record = self.dataset[min(self.dataset_idx + 1, self.dataset_len - 1)]
        self.predicted_app = next_record["target_app"]

        if self.battery_level < 0.2:
            reward -= 0.2
        if self.ram_usage > 0.85:
            reward -= 0.2
        reward -= self.thrashing_count * 0.005

        terminated = self.current_step >= self.max_steps
        truncated = False
        return self._get_obs(), reward, terminated, truncated, {}
