"""Train an LSTM exercise classifier on the 30-frame pose sequences (PyTorch, CPU).

Unlike the Random Forest baseline (train_classifier.py), which only sees a summary of
each sequence, the LSTM reads the 30 frames in order, so it can use the movement itself.

Architecture (from the roadmap):
    66 values per frame -> LSTM (64 units) -> Dropout (0.5) -> Dense (32) -> 3 exercises

Uses the same video splits as the baseline, so the results can be compared directly.

Usage (from the project root, with .venv activated):
    python src/train_lstm.py
"""
import argparse
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch import nn

from train_classifier import PROJECT_ROOT, SEED, load_sequences, split_by_video

EPOCHS = 40
BATCH_SIZE = 32
LEARNING_RATE = 1e-3


class ExerciseLSTM(nn.Module):
    def __init__(self, n_features, n_classes, hidden=64):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, batch_first=True)
        self.head = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(hidden, 32),
            nn.ReLU(),
            nn.Linear(32, n_classes),
        )

    def forward(self, x):
        # x: (batch, frames, features). The LSTM's state after the last frame
        # summarizes the whole sequence.
        _, (last_hidden, _) = self.lstm(x)
        return self.head(last_hidden[-1])


def train_model(X, y, n_classes, epochs=EPOCHS, seed=SEED):
    """Train a fresh LSTM on X (sequences, frames, features) and labels y."""
    torch.manual_seed(seed)
    model = ExerciseLSTM(X.shape[2], n_classes)
    # Weight each exercise by 1 / (its number of sequences), like class_weight="balanced".
    counts = np.bincount(y, minlength=n_classes)
    weights = torch.tensor(len(y) / (n_classes * counts), dtype=torch.float32)
    loss_fn = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    X_t, y_t = torch.from_numpy(X), torch.from_numpy(y).long()
    generator = torch.Generator().manual_seed(seed)
    model.train()
    for epoch in range(epochs):
        order = torch.randperm(len(X_t), generator=generator)
        total_loss = 0.0
        for start in range(0, len(order), BATCH_SIZE):
            batch = order[start:start + BATCH_SIZE]
            optimizer.zero_grad()
            loss = loss_fn(model(X_t[batch]), y_t[batch])
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(batch)
        if (epoch + 1) % 10 == 0:
            print(f"  epoch {epoch + 1:3d}/{epochs}  loss {total_loss / len(X_t):.4f}")
    return model


def predict(model, X):
    model.eval()
    with torch.no_grad():
        return model(torch.from_numpy(X)).argmax(dim=1).numpy()


def load_lstm(path):
    """Load a model saved by this script; returns (model, class names)."""
    saved = torch.load(path)
    model = ExerciseLSTM(saved["n_features"], len(saved["classes"]))
    model.load_state_dict(saved["state_dict"])
    model.eval()
    return model, saved["classes"]


def main():
    parser = argparse.ArgumentParser(description="Train the LSTM exercise classifier")
    parser.add_argument("--data", type=Path, default=PROJECT_ROOT / "data" / "sequences.npz")
    parser.add_argument("--output", type=Path,
                        default=PROJECT_ROOT / "models" / "exercise_classifier_lstm.pt")
    args = parser.parse_args()

    X, y, videos, classes = load_sequences(args.data)
    splits = list(split_by_video(y, videos))

    # Main result: the first split, same as the baseline.
    train, test = splits[0]
    print(f"Train: {len(set(videos[train]))} videos, {len(train)} sequences")
    print(f"Test:  {len(set(videos[test]))} videos, {len(test)} sequences")
    print("Training on split 1:")
    model = train_model(X[train], y[train], len(classes))
    predicted = predict(model, X[test])

    print(f"\nTest accuracy: {accuracy_score(y[test], predicted):.1%}\n")
    print(classification_report(y[test], predicted, target_names=classes, digits=3))
    print("Confusion matrix (rows = true exercise, columns = predicted):")
    print(f"{'':8s}" + "".join(f"{name:>8s}" for name in classes))
    for name, row in zip(classes, confusion_matrix(y[test], predicted)):
        print(f"{name:8s}" + "".join(f"{count:8d}" for count in row))

    # Cross-check on all 3 video splits (split 1 is already done above).
    scores = [accuracy_score(y[test], predicted)]
    for n, (fold_train, fold_test) in enumerate(splits[1:], start=2):
        print(f"\nTraining on split {n}:")
        fold_model = train_model(X[fold_train], y[fold_train], len(classes))
        scores.append(accuracy_score(y[fold_test], predict(fold_model, X[fold_test])))
    print(f"\nAccuracy on each of the {len(splits)} video splits: "
          + ", ".join(f"{s:.1%}" for s in scores)
          + f"  (mean {np.mean(scores):.1%})")

    # Final model: trained on all videos, saved for later use.
    print("\nTraining final model on all videos:")
    final = train_model(X, y, len(classes))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": final.state_dict(), "classes": classes,
                "n_features": X.shape[2]}, args.output)
    print(f"Saved model to {args.output}")


if __name__ == "__main__":
    main()
