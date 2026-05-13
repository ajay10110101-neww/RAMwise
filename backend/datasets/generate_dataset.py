import pandas as pd
import random
import json
from datetime import datetime, timedelta

# =========================================================
# LOAD REAL DATASET
# =========================================================

df = pd.read_csv(
    "screen_time_app_usage_dataset.csv"
)

# =========================================================
# APP STATISTICS FROM REAL DATASET
# =========================================================

app_stats = {}

for app in df["app_name"].unique():

    app_df = df[
        df["app_name"] == app
    ]

    avg_screen_time = (
        app_df["screen_time_min"]
        .mean()
    )

    avg_launches = (
        app_df["launches"]
        .mean()
    )

    avg_interactions = (
        app_df["interactions"]
        .mean()
    )

    category = (
        app_df["category"]
        .mode()[0]
    )

    productive = bool(
        app_df["is_productive"]
        .mode()[0]
    )

    app_stats[app] = {

        "screen_time":
            avg_screen_time,

        "launches":
            avg_launches,

        "interactions":
            avg_interactions,

        "category":
            category,

        "productive":
            productive
    }

# =========================================================
# APP RAM PROFILES
# =========================================================

APP_PROFILES = {

    "Chrome": {
        "ram": (700, 1800),
        "cpu": (20, 70)
    },

    "Instagram": {
        "ram": (500, 1400),
        "cpu": (20, 65)
    },

    "YouTube": {
        "ram": (1200, 2500),
        "cpu": (40, 95)
    },

    "Spotify": {
        "ram": (250, 600),
        "cpu": (10, 35)
    },

    "WhatsApp": {
        "ram": (250, 700),
        "cpu": (10, 40)
    },

    "Google Maps": {
        "ram": (700, 1800),
        "cpu": (30, 85)
    },

    "Gmail": {
        "ram": (300, 700),
        "cpu": (10, 40)
    },

    "Slack": {
        "ram": (500, 1000),
        "cpu": (15, 45)
    },

    "Notion": {
        "ram": (400, 900),
        "cpu": (10, 35)
    }
}

DEFAULT_PROFILE = {
    "ram": (300, 900),
    "cpu": (10, 50)
}

# =========================================================
# PERSONA-BASED SESSIONS
# =========================================================

PERSONAS = {

    "student": [

        "WhatsApp",
        "Instagram",
        "YouTube",
        "Spotify",
        "Chrome",

        "WhatsApp",
        "Instagram",
        "YouTube",

        "Spotify",
        "Chrome"
    ],

    "office_worker": [

        "Gmail",
        "Chrome",
        "Slack",
        "Notion",
        "Google Docs",

        "Gmail",
        "Slack",
        "Chrome",

        "Notion"
    ],

    "traveler": [

        "Google Maps",
        "Spotify",
        "WhatsApp",
        "Chrome",

        "Google Maps",
        "WhatsApp",

        "Spotify"
    ],

    "content_creator": [

        "Instagram",
        "Camera",
        "YouTube",
        "Twitter",

        "Chrome",
        "Instagram",

        "YouTube"
    ]
}

# =========================================================
# HELPERS
# =========================================================

TOTAL_RAM_MB = 8192


def classify_memory_pressure(
    ram_percent
):

    if ram_percent < 50:
        return "LOW"

    elif ram_percent < 80:
        return "MEDIUM"

    return "HIGH"


def classify_cache_state(
    ram_percent,
    battery_level
):

    if ram_percent > 80:
        return "COLD"

    elif ram_percent > 60:
        return "WARM"

    return "HOT"


def generate_latency(
    cache_state
):

    if cache_state == "HOT":
        return random.randint(100, 350)

    elif cache_state == "WARM":
        return random.randint(400, 1200)

    return random.randint(1200, 3500)


def get_time_bucket(hour):

    if 5 <= hour < 12:
        return "MORNING"

    elif 12 <= hour < 17:
        return "AFTERNOON"

    elif 17 <= hour < 22:
        return "EVENING"

    return "NIGHT"


def generate_rl_action(
    memory_pressure,
    cache_state
):

    if memory_pressure == "HIGH":

        return random.choice([

            "EVICT",

            "COMPRESS",

            "DEMOTE_WARM"
        ])

    if cache_state == "HOT":

        return random.choice([

            "PRELOAD",

            "PROMOTE_HOT",

            "NO_ACTION"
        ])

    return "NO_ACTION"

# =========================================================
# GENERATE DATASET
# =========================================================

records = []

start_time = datetime.now()

record_id = 0

for user_id in range(1000, 1300):

    persona_name = random.choice(
        list(PERSONAS.keys())
    )

    session_pattern = PERSONAS[
        persona_name
    ]

    for _ in range(10):

        session = session_pattern.copy()

        if random.random() > 0.5:
            random.shuffle(session)

        for i in range(len(session) - 3):

            app_sequence = [

                session[i],
                session[i + 1],
                session[i + 2]
            ]

            target_app = session[i + 3]

            current_app = session[i + 2]

            stats = app_stats.get(
                current_app,
                {
                    "screen_time": 10,
                    "launches": 2,
                    "interactions": 5,
                    "category": "General",
                    "productive": False
                }
            )

            profile = APP_PROFILES.get(
                current_app,
                DEFAULT_PROFILE
            )

            app_ram_usage = random.randint(
                profile["ram"][0],
                profile["ram"][1]
            )

            cpu_usage = random.randint(
                profile["cpu"][0],
                profile["cpu"][1]
            )

            ram_used_mb = random.randint(
                3000,
                7800
            )

            ram_percent = int(
                (ram_used_mb / TOTAL_RAM_MB)
                * 100
            )

            ram_free_mb = (
                TOTAL_RAM_MB - ram_used_mb
            )

            battery_level = random.randint(
                10,
                100
            )

            charging_state = random.choice(
                [True, False]
            )

            thermal_state = random.choice([

                "NORMAL",

                "WARM",

                "HOT"
            ])

            network_type = random.choice([

                "WiFi",

                "4G",

                "5G"
            ])

            background_apps = random.randint(
                2,
                15
            )

            memory_pressure = (
                classify_memory_pressure(
                    ram_percent
                )
            )

            cache_state = (
                classify_cache_state(
                    ram_percent,
                    battery_level
                )
            )

            cache_hit = (
                cache_state == "HOT"
                and random.random() > 0.2
            )

            launch_latency_ms = (
                generate_latency(
                    cache_state
                )
            )

            baseline_lru_latency_ms = (
                launch_latency_ms
                + random.randint(200, 1200)
            )

            latency_improvement_percent = round(

                (
                    baseline_lru_latency_ms
                    - launch_latency_ms
                )

                /

                baseline_lru_latency_ms

                * 100,

                2
            )

            rl_action = generate_rl_action(

                memory_pressure,

                cache_state
            )

            timestamp = (
                start_time
                + timedelta(
                    minutes=record_id * 5
                )
            )

            record = {

                "user_id":
                    user_id,

                "persona":
                    persona_name,

                "app_sequence":
                    app_sequence,

                "target_app":
                    target_app,

                "current_app":
                    current_app,

                "category":
                    stats["category"],

                "screen_time_min":

                    round(
                        stats["screen_time"]
                        *
                        random.uniform(
                            0.7,
                            1.3
                        ),
                        2
                    ),

                "launches":

                    max(
                        1,
                        int(
                            stats["launches"]
                            *
                            random.uniform(
                                0.5,
                                1.5
                            )
                        )
                    ),

                "interactions":

                    max(
                        1,
                        int(
                            stats["interactions"]
                            *
                            random.uniform(
                                0.5,
                                1.5
                            )
                        )
                    ),

                "is_productive":
                    stats["productive"],

                "app_ram_usage_mb":
                    app_ram_usage,

                "ram_used_mb":
                    ram_used_mb,

                "ram_free_mb":
                    ram_free_mb,

                "ram_usage_percent":
                    ram_percent,

                "cpu_usage_percent":
                    cpu_usage,

                "battery_level":
                    battery_level,

                "charging_state":
                    charging_state,

                "thermal_state":
                    thermal_state,

                "network_type":
                    network_type,

                "background_apps":
                    background_apps,

                "memory_pressure":
                    memory_pressure,

                "cache_state":
                    cache_state,

                "cache_hit":
                    cache_hit,

                "launch_latency_ms":
                    launch_latency_ms,

                "baseline_lru_latency_ms":
                    baseline_lru_latency_ms,

                "latency_improvement_percent":
                    latency_improvement_percent,

                "rl_action":
                    rl_action,

                "hour_of_day":
                    timestamp.hour,

                "day_of_week":
                    timestamp.strftime("%A"),

                "time_bucket":
                    get_time_bucket(
                        timestamp.hour
                    ),

                "timestamp":
                    str(timestamp)
            }

            records.append(record)

            record_id += 1

# =========================================================
# SAVE
# =========================================================

with open(
    "synthetic_dataset.json",
    "w"
) as f:

    json.dump(
        records,
        f,
        indent=2
    )

print(
    f"Generated {len(records)} records."
)