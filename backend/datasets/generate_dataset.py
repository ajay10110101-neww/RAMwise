import json
import random


def get_app_tokens():
    return {
        "Chrome": 1,
        "WhatsApp": 2,
        "Instagram": 3,
        "Spotify": 4,
        "YouTube": 5,
        "Maps": 6,
        "Gmail": 7,
        "Twitter": 8,
        "Netflix": 9,
        "Camera": 10,
        "Photos": 11,
        "Settings": 12,
        "Calculator": 13,
        "Calendar": 14,
        "Files": 15
    }


def get_transition_sequences():
    return [
        ["Chrome", "WhatsApp", "Instagram", "Spotify"],
        ["Maps", "Spotify", "Chrome", "WhatsApp"],
        ["YouTube", "Instagram", "Twitter", "Chrome"],
        ["Gmail", "Chrome", "Calendar", "WhatsApp"],
        ["Camera", "Photos", "Instagram", "WhatsApp"],
        ["Netflix", "YouTube", "Spotify", "Chrome"],
        ["Maps", "Gmail", "Chrome", "Calendar"],
        ["WhatsApp", "Instagram", "Camera", "Photos"],
        ["Spotify", "YouTube", "Netflix", "Chrome"],
        ["Calculator", "Files", "Chrome", "Gmail"]
    ]


def classify_memory_pressure(ram_usage):
    if ram_usage < 60:
        return "LOW"
    elif ram_usage <= 80:
        return "MEDIUM"
    else:
        return "HIGH"


def classify_cache_state(ram_usage, battery_level):
    if ram_usage > 80 or battery_level < 20:
        return "COLD"
    elif ram_usage >= 60:
        return "WARM"
    else:
        if battery_level > 50:
            return "HOT"
        else:
            return "WARM"


def generate_latency(cache_state):
    if cache_state == "HOT":
        return round(random.uniform(0.1, 0.5), 2)
    elif cache_state == "WARM":
        return round(random.uniform(0.5, 1.2), 2)
    else:
        return round(random.uniform(1.2, 3.0), 2)


def generate_preload_event(cache_state, battery_level):
    return cache_state == "HOT" and battery_level > 40


def generate_eviction_event(memory_pressure):
    return memory_pressure == "HIGH"


def generate_records(num_records, sequences):
    records = []
    timestamp = 1700000000

    for _ in range(num_records):
        seq = random.choice(sequences)
        app_sequence = seq[:3]

        ram_usage = random.randint(45, 95)
        battery_level = random.randint(10, 100)
        cpu_usage = random.randint(10, 85)

        memory_pressure = classify_memory_pressure(ram_usage)
        cache_state = classify_cache_state(ram_usage, battery_level)
        latency = generate_latency(cache_state)
        preload_event = generate_preload_event(cache_state, battery_level)
        eviction_event = generate_eviction_event(memory_pressure)

        timestamp += random.randint(3, 10)

        record = {
            "app_sequence": app_sequence,
            "ram_usage": ram_usage,
            "battery_level": battery_level,
            "cpu_usage": cpu_usage,
            "memory_pressure": memory_pressure,
            "cache_state": cache_state,
            "latency": latency,
            "preload_event": preload_event,
            "eviction_event": eviction_event,
            "timestamp": timestamp
        }
        records.append(record)

    return records


def save_dataset(records, filepath):
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2)


def main():
    sequences = get_transition_sequences()
    records = generate_records(2000, sequences)
    save_dataset(records, "synthetic_dataset.json")
    print("Dataset generation complete. Total records: 2000")


if __name__ == "__main__":
    main()
