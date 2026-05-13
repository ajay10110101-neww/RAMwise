import json
import torch
import numpy as np

from torch.utils.data import (
    Dataset,
    DataLoader
)

from sklearn.model_selection import (
    train_test_split
)

from sklearn.metrics import accuracy_score

from model import AppTransformer

# =========================================================
# CONFIG
# =========================================================

BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 1e-3

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

# =========================================================
# LOAD DATA
# =========================================================

with open(
    "../datasets/processed_dataset.json",
    "r"
) as f:

    data = json.load(f)

with open(
    "../datasets/tokenizer.json",
    "r"
) as f:

    tokenizer = json.load(f)

VOCAB_SIZE = len(tokenizer)
NUM_CLASSES = len(tokenizer)

# =========================================================
# BUILD FEATURES
# =========================================================

X_tokens = []
X_context = []
y = []

for record in data:

    X_tokens.append(
        record["token_sequence"]
    )

    # =====================================================
    # CLEANER CONTEXT FEATURES
    # =====================================================

    context = [

        record["screen_time_normalized"],

        record["launches_normalized"],

        record["ram_percent_normalized"],

        record["cpu_normalized"],

        record["battery_normalized"],

        record["hour_normalized"],

        record["cache_state"]
    ]

    X_context.append(context)

    y.append(record["target_app"])

# =========================================================
# NUMPY CONVERSION
# =========================================================

X_tokens = np.array(X_tokens)

X_context = np.array(
    X_context,
    dtype=np.float32
)

y = np.array(y)

# =========================================================
# TRAIN TEST SPLIT
# =========================================================

(
    X_tokens_train,
    X_tokens_test,
    X_context_train,
    X_context_test,
    y_train,
    y_test
) = train_test_split(

    X_tokens,
    X_context,
    y,

    test_size=0.2,

    random_state=42
)

# =========================================================
# DATASET CLASS
# =========================================================

class RAMWiseDataset(Dataset):

    def __init__(
        self,
        token_sequences,
        context_features,
        labels
    ):

        self.token_sequences = torch.tensor(
            token_sequences,
            dtype=torch.long
        )

        self.context_features = torch.tensor(
            context_features,
            dtype=torch.float32
        )

        self.labels = torch.tensor(
            labels,
            dtype=torch.long
        )

    def __len__(self):

        return len(self.labels)

    def __getitem__(self, idx):

        return (

            self.token_sequences[idx],

            self.context_features[idx],

            self.labels[idx]
        )

# =========================================================
# DATA LOADERS
# =========================================================

train_dataset = RAMWiseDataset(

    X_tokens_train,

    X_context_train,

    y_train
)

test_dataset = RAMWiseDataset(

    X_tokens_test,

    X_context_test,

    y_test
)

train_loader = DataLoader(

    train_dataset,

    batch_size=BATCH_SIZE,

    shuffle=True
)

test_loader = DataLoader(

    test_dataset,

    batch_size=BATCH_SIZE
)

# =========================================================
# MODEL
# =========================================================

model = AppTransformer(

    vocab_size=VOCAB_SIZE,

    num_classes=NUM_CLASSES,

    context_dim=7
).to(DEVICE)

# =========================================================
# LOSS + OPTIMIZER
# =========================================================

criterion = torch.nn.CrossEntropyLoss()

optimizer = torch.optim.Adam(

    model.parameters(),

    lr=LEARNING_RATE
)

# =========================================================
# TRAINING
# =========================================================

print("\nStarting training...\n")

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0

    for (

        token_seq,

        context_features,

        labels

    ) in train_loader:

        token_seq = token_seq.to(DEVICE)

        context_features = (
            context_features.to(DEVICE)
        )

        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(

            token_seq,

            context_features
        )

        loss = criterion(
            outputs,
            labels
        )

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    avg_loss = (
        total_loss / len(train_loader)
    )

    print(

        f"Epoch [{epoch+1}/{EPOCHS}] "
        f"Loss: {avg_loss:.4f}"
    )

# =========================================================
# EVALUATION
# =========================================================

model.eval()

predictions = []
actuals = []

with torch.no_grad():

    for (

        token_seq,

        context_features,

        labels

    ) in test_loader:

        token_seq = token_seq.to(DEVICE)

        context_features = (
            context_features.to(DEVICE)
        )

        outputs = model(

            token_seq,

            context_features
        )

        preds = torch.argmax(
            outputs,
            dim=1
        )

        predictions.extend(
            preds.cpu().numpy()
        )

        actuals.extend(
            labels.numpy()
        )

accuracy = accuracy_score(
    actuals,
    predictions
)

print(
    f"\nTest Accuracy: "
    f"{accuracy * 100:.2f}%"
)

# =========================================================
# SAVE MODEL
# =========================================================

torch.save(

    model.state_dict(),

    "../../models/transformer_weights/app_transformer.pth"
)

print(
    "\nModel saved successfully.\n"
)