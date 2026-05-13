import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import os
import random
import numpy as np
from model import AppTransformer, get_topk_predictions
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

VOCAB_SIZE = 17
EMBED_DIM = 64
NUM_HEADS = 4
NUM_LAYERS = 2
NUM_CLASSES = 16
DROPOUT = 0.1
MAX_SEQ_LEN = 10
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 30
DEVICE = torch.device("cpu")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "..", "datasets", "processed_dataset.json")
MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, "..", "..", "models", "transformer_weights", "transformer_model.pt")
METRICS_SAVE_PATH = os.path.join(SCRIPT_DIR, "..", "..", "models", "transformer_weights", "training_metrics.json")


class AppSequenceDataset(Dataset):
    def __init__(self, records):
        self.records = records

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        record = self.records[idx]
        token_seq = record["token_sequence"][:2]
        context = [
            record["ram_normalized"],
            record["battery_normalized"],
            record["cpu_normalized"],
            record["cache_encoded"] / 2.0,
        ]
        label = record["token_sequence"][-1] - 1
        return {
            "token_seq": torch.tensor(token_seq, dtype=torch.long),
            "context": torch.tensor(context, dtype=torch.float32),
            "label": torch.tensor(label, dtype=torch.long),
        }


def load_dataset(path):
    with open(path, "r") as f:
        data = json.load(f)
    valid = [
        r for r in data if all(t != 0 and t != 16 for t in r["token_sequence"])
    ]
    print(f"Loaded {len(valid)} valid records from dataset")
    return valid


def train_one_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    num_batches = 0
    for batch in dataloader:
        token_seq = batch["token_seq"].to(device)
        context = batch["context"].to(device)
        label = batch["label"].to(device)
        optimizer.zero_grad()
        output = model(token_seq, context)
        loss = criterion(output, label)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        num_batches += 1
    return total_loss / num_batches


def evaluate(model, dataloader, device):
    model.eval()
    all_preds = []
    all_labels = []
    top3_correct = 0
    total = 0
    with torch.no_grad():
        for batch in dataloader:
            token_seq = batch["token_seq"].to(device)
            context = batch["context"].to(device)
            label = batch["label"].to(device)
            output = model(token_seq, context)
            top3_indices = torch.topk(output, 3, dim=1).indices
            preds = output.argmax(dim=1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(label.cpu().tolist())
            for i in range(label.size(0)):
                if label[i].item() in top3_indices[i].cpu().tolist():
                    top3_correct += 1
            total += label.size(0)
    top1_acc = accuracy_score(all_labels, all_preds) * 100
    top3_acc = (top3_correct / total) * 100
    model.train()
    return {"top1_accuracy": top1_acc, "top3_accuracy": top3_acc}


if __name__ == "__main__":
    data = load_dataset(DATASET_PATH)
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
    train_dataset = AppSequenceDataset(train_data)
    test_dataset = AppSequenceDataset(test_data)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = AppTransformer(
        vocab_size=VOCAB_SIZE,
        embed_dim=EMBED_DIM,
        num_heads=NUM_HEADS,
        num_layers=NUM_LAYERS,
        num_classes=NUM_CLASSES,
        dropout=DROPOUT,
        max_seq_len=MAX_SEQ_LEN,
    ).to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    train_losses = []
    top1_accs = []
    top3_accs = []

    for epoch in range(1, EPOCHS + 1):
        loss = train_one_epoch(model, train_loader, optimizer, criterion, DEVICE)
        metrics = evaluate(model, test_loader, DEVICE)
        scheduler.step()
        train_losses.append(loss)
        top1_accs.append(metrics["top1_accuracy"])
        top3_accs.append(metrics["top3_accuracy"])
        print(
            f"Epoch {epoch}/{EPOCHS} | Loss: {loss:.4f} | Top-1: {metrics['top1_accuracy']:.2f}% | Top-3: {metrics['top3_accuracy']:.2f}%"
        )

    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    torch.save(model.state_dict(), MODEL_SAVE_PATH)

    metrics_data = {
        "final_top1_accuracy": top1_accs[-1],
        "final_top3_accuracy": top3_accs[-1],
        "final_loss": train_losses[-1],
        "epochs": EPOCHS,
        "train_size": len(train_data),
        "test_size": len(test_data),
        "all_losses": train_losses,
        "all_top1": top1_accs,
        "all_top3": top3_accs,
    }
    with open(METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics_data, f, indent=2)

    print("Model saved to models/transformer_weights/transformer_model.pt")
    print(
        f"Final Top-1 Accuracy: {top1_accs[-1]:.2f}% | Final Top-3 Accuracy: {top3_accs[-1]:.2f}%"
    )
