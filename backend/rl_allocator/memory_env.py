import gymnasium as gym
from gymnasium.spaces import Box, Discrete
import numpy as np
import random


class MemoryEnv(gym.Env):

    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.num_apps = 15
        self.cache_size = 5
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

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.ram_usage = random.uniform(0.4, 0.9)
        self.battery_level = random.uniform(0.2, 1.0)
        self.cpu_usage = random.uniform(0.1, 0.8)
        all_apps = list(range(1, 16))
        random.shuffle(all_apps)
        self.hot_apps = set(all_apps[:2])
        self.warm_apps = set(all_apps[2:5])
        self.cold_apps = set(all_apps[5:])
        self.current_step = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.thrashing_count = 0
        self.predicted_app = random.randint(1, 15)
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
                self.current_step / self.max_steps,
            ],
            dtype=np.float32,
        )

    def step(self, action):
        self.current_step += 1
        reward = 0.0

        launched_app = random.randint(1, 15)
        if launched_app in self.hot_apps:
            self.cache_hits += 1
            reward += 1.0
            launch_latency = random.uniform(0.1, 0.5)
        elif launched_app in self.warm_apps:
            self.cache_hits += 1
            reward += 0.3
            launch_latency = random.uniform(0.5, 1.2)
        else:
            self.cache_misses += 1
            reward -= 0.5
            launch_latency = random.uniform(1.2, 3.0)

        if action == 0:
            if self.battery_level > 0.4 and len(self.hot_apps) < self.cache_size:
                self.hot_apps.add(self.predicted_app)
                self.warm_apps.discard(self.predicted_app)
                self.cold_apps.discard(self.predicted_app)
                reward += 0.5
            else:
                reward -= 0.2

        elif action == 1:
            if len(self.hot_apps) > 0:
                evicted = random.choice(list(self.hot_apps))
                self.hot_apps.remove(evicted)
                self.cold_apps.add(evicted)
                self.thrashing_count += 1
                reward -= 0.3
            else:
                reward -= 0.1

        elif action == 2:
            if len(self.warm_apps) > 0 and len(self.hot_apps) < self.cache_size:
                app = random.choice(list(self.warm_apps))
                self.warm_apps.remove(app)
                self.hot_apps.add(app)
                reward += 0.4
            else:
                reward -= 0.1

        elif action == 3:
            if len(self.cold_apps) > 0:
                app = random.choice(list(self.cold_apps))
                self.cold_apps.remove(app)
                self.warm_apps.add(app)
                reward += 0.2
            else:
                reward -= 0.05

        elif action == 4:
            if len(self.hot_apps) > 0:
                app = random.choice(list(self.hot_apps))
                self.hot_apps.remove(app)
                self.cold_apps.add(app)
                if self.ram_usage > 0.8:
                    reward += 0.3
                else:
                    reward -= 0.2
            else:
                reward -= 0.05

        self.ram_usage = max(0.1, min(1.0, self.ram_usage + random.uniform(-0.05, 0.05)))
        self.battery_level = max(0.0, min(1.0, self.battery_level - random.uniform(0.001, 0.005)))
        self.cpu_usage = max(0.05, min(1.0, self.cpu_usage + random.uniform(-0.1, 0.1)))
        self.predicted_app = random.randint(1, 15)

        if self.battery_level < 0.2:
            reward -= 0.3

        if self.ram_usage > 0.85:
            reward -= 0.4

        reward -= self.thrashing_count * 0.01

        terminated = self.current_step >= self.max_steps
        truncated = False

        return self._get_obs(), reward, terminated, truncated, {}
