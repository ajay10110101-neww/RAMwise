import json


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


def build_tokenizer(app_tokens):
    tokenizer = {"PAD": 0, "UNKNOWN": 16}
    for app, token in app_tokens.items():
        tokenizer[app] = token
    return tokenizer


def tokenize_sequence(app_sequence, tokenizer):
    return [tokenizer.get(app, tokenizer["UNKNOWN"]) for app in app_sequence]


def encode_cache_state(cache_state):
    mapping = {"HOT": 2, "WARM": 1, "COLD": 0}
    return mapping[cache_state]


def encode_memory_pressure(memory_pressure):
    mapping = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
    return mapping[memory_pressure]


def process_record(record, tokenizer):
    token_sequence = tokenize_sequence(record["app_sequence"], tokenizer)
    ram_normalized = record["ram_usage"] / 100.0
    battery_normalized = record["battery_level"] / 100.0
    cpu_normalized = record["cpu_usage"] / 100.0
    cache_encoded = encode_cache_state(record["cache_state"])
    memory_pressure_encoded = encode_memory_pressure(record["memory_pressure"])

    return {
        "token_sequence": token_sequence,
        "ram_normalized": ram_normalized,
        "battery_normalized": battery_normalized,
        "cpu_normalized": cpu_normalized,
        "cache_encoded": cache_encoded,
        "memory_pressure_encoded": memory_pressure_encoded,
        "latency": record["latency"],
        "preload_event": record["preload_event"],
        "eviction_event": record["eviction_event"],
        "timestamp": record["timestamp"]
    }


def load_dataset(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(data, filepath):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def save_tokenizer(tokenizer, filepath):
    save_json(tokenizer, filepath)


def main():
    app_tokens = get_app_tokens()
    tokenizer = build_tokenizer(app_tokens)

    raw_data = load_dataset("synthetic_dataset.json")

    processed = [process_record(record, tokenizer) for record in raw_data]

    save_json(processed, "processed_dataset.json")
    save_tokenizer(tokenizer, "tokenizer.json")

    print(f"Preprocessing complete. Processed records: {len(processed)}. Tokenizer saved.")


if __name__ == "__main__":
    main()
