class AdaptiveCache:
    def __init__(self, hot_size=3, warm_size=5):
        self.hot = []
        self.warm = []
        self.cold = set()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.preloads = 0
        self.hot_size = hot_size
        self.warm_size = warm_size

    def access(self, app, ram_usage=0.5, battery_level=0.6, predicted_next=None):
        if app in self.hot:
            self.hits += 1
            self.hot.remove(app)
            self.hot.insert(0, app)
            latency = 0.1
            return {"hit": True, "tier": "HOT", "latency": latency}
        elif app in self.warm:
            self.hits += 1
            self.warm.remove(app)
            if len(self.hot) >= self.hot_size:
                demoted = self.hot.pop()
                self.warm.insert(0, demoted)
            self.hot.insert(0, app)
            latency = 0.4
            return {"hit": True, "tier": "WARM", "latency": latency}
        else:
            self.misses += 1
            self.cold.discard(app)
            if len(self.hot) >= self.hot_size:
                demoted = self.hot.pop()
                self.evictions += 1
                if len(self.warm) >= self.warm_size:
                    evicted_from_warm = self.warm.pop()
                    self.cold.add(evicted_from_warm)
                self.warm.insert(0, demoted)
            self.hot.insert(0, app)
            latency = 1.8
            return {"hit": False, "tier": "COLD", "latency": latency}

    def preload(self, app, battery_level=0.6):
        if battery_level > 0.4 and app not in self.hot and app not in self.warm:
            self.warm.insert(0, app)
            if len(self.warm) > self.warm_size:
                overflow = self.warm.pop()
                self.cold.add(overflow)
            self.preloads += 1
            return True
        return False

    def get_stats(self):
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "preloads": self.preloads,
            "hit_rate": round(hit_rate, 4),
            "total_accesses": total,
        }

    def reset(self):
        self.hot = []
        self.warm = []
        self.cold = set()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.preloads = 0


class LRUCache:
    def __init__(self, capacity=8):
        self.cache = []
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def access(self, app):
        if app in self.cache:
            self.hits += 1
            self.cache.remove(app)
            self.cache.insert(0, app)
            latency = 0.5
            return {"hit": True, "latency": latency}
        else:
            self.misses += 1
            if len(self.cache) >= self.capacity:
                self.cache.pop()
                self.evictions += 1
            self.cache.insert(0, app)
            latency = 1.8
            return {"hit": False, "latency": latency}

    def get_stats(self):
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 4),
            "total_accesses": total,
        }

    def reset(self):
        self.cache = []
        self.hits = 0
        self.misses = 0
        self.evictions = 0
