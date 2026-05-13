import json

# =========================================================
# TOKENIZERS
# =========================================================

APP_TOKENIZER = {
    "PAD": 0,
    "UNKNOWN": 1
}

CACHE_TOKENIZER = {
    "COLD": 0,
    "WARM": 1,
    "HOT": 2
}

PRESSURE_TOKENIZER = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2
}

THERMAL_TOKENIZER = {
    "NORMAL": 0,
    "WARM": 1,
    "HOT": 2
}

NETWORK_TOKENIZER = {
    "WiFi": 0,
    "4G": 1,
    "5G": 2
}

TIME_BUCKET_TOKENIZER = {
    "MORNING": 0,
    "AFTERNOON": 1,
    "EVENING": 2,
    "NIGHT": 3
}

RL_ACTION_TOKENIZER = {
    "NO_ACTION": 0,
    "PRELOAD": 1,
    "PROMOTE_HOT": 2,
    "DEMOTE_WARM": 3,
    "COMPRESS": 4,
    "EVICT": 5
}

# =========================================================
# LOAD DATA
# =========================================================

with open(
    "synthetic_dataset.json",
    "r"
) as f:

    data = json.load(f)

# =========================================================
# BUILD APP TOKENIZER
# =========================================================

unique_apps = set()

for record in data:

    unique_apps.update(
        record["app_sequence"]
    )

    unique_apps.add(
        record["target_app"]
    )

for idx, app in enumerate(
    sorted(unique_apps),
    start=2
):

    APP_TOKENIZER[app] = idx

# =========================================================
# HELPERS
# =========================================================

def tokenize_apps(sequence):

    return [

        APP_TOKENIZER.get(app, 1)

        for app in sequence
    ]


def normalize(value, max_value):

    return value / max_value

# =========================================================
# PROCESS DATA
# =========================================================

processed = []

for record in data:

    processed_record = {

        "token_sequence":

            tokenize_apps(
                record["app_sequence"]
            ),

        "target_app":

            APP_TOKENIZER.get(
                record["target_app"],
                1
            ),

        # =========================================
        # NORMALIZED NUMERICAL FEATURES
        # =========================================

        "screen_time_normalized":

            normalize(
                record["screen_time_min"],
                300
            ),

        "launches_normalized":

            normalize(
                record["launches"],
                20
            ),

        "interactions_normalized":

            normalize(
                record["interactions"],
                100
            ),

        "app_ram_normalized":

            normalize(
                record["app_ram_usage_mb"],
                4000
            ),

        "ram_used_normalized":

            normalize(
                record["ram_used_mb"],
                8192
            ),

        "ram_free_normalized":

            normalize(
                record["ram_free_mb"],
                8192
            ),

        "ram_percent_normalized":

            normalize(
                record["ram_usage_percent"],
                100
            ),

        "cpu_normalized":

            normalize(
                record["cpu_usage_percent"],
                100
            ),

        "battery_normalized":

            normalize(
                record["battery_level"],
                100
            ),

        "background_apps_normalized":

            normalize(
                record["background_apps"],
                20
            ),

        "hour_normalized":

            normalize(
                record["hour_of_day"],
                24
            ),

        # =========================================
        # BOOLEAN FEATURES
        # =========================================

        "charging_state":

            int(record["charging_state"]),

        "cache_hit":

            int(record["cache_hit"]),

        "is_productive":

            int(record["is_productive"]),

        # =========================================
        # ENCODED CATEGORICALS
        # =========================================

        "cache_state":

            CACHE_TOKENIZER[
                record["cache_state"]
            ],

        "memory_pressure":

            PRESSURE_TOKENIZER[
                record["memory_pressure"]
            ],

        "thermal_state":

            THERMAL_TOKENIZER[
                record["thermal_state"]
            ],

        "network_type":

            NETWORK_TOKENIZER[
                record["network_type"]
            ],

        "time_bucket":

            TIME_BUCKET_TOKENIZER[
                record["time_bucket"]
            ],

        "rl_action":

            RL_ACTION_TOKENIZER[
                record["rl_action"]
            ],

        # =========================================
        # TARGET METRICS
        # =========================================

        "launch_latency_ms":

            record["launch_latency_ms"],

        "baseline_lru_latency_ms":

            record[
                "baseline_lru_latency_ms"
            ],

        "latency_improvement_percent":

            record[
                "latency_improvement_percent"
            ]
    }

    processed.append(
        processed_record
    )

# =========================================================
# SAVE
# =========================================================

with open(
    "processed_dataset.json",
    "w"
) as f:

    json.dump(
        processed,
        f,
        indent=2
    )

with open(
    "tokenizer.json",
    "w"
) as f:

    json.dump(
        APP_TOKENIZER,
        f,
        indent=2
    )

print(
    f"Processed {len(processed)} records."
)