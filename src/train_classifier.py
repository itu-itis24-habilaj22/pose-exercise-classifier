"""Train a baseline exercise classifier (Random Forest) on the 30-frame pose sequences.

Each sequence (30 frames x 66 values) is summarized by the mean, standard deviation,
min and max of every value over the 30 frames -> 264 numbers, and a Random Forest
learns from those. This is the baseline the LSTM will be compared with.

Train/test is split by video (about 70/30, same exercise mix in both): windows of one
video overlap, so letting them land on both sides would make the test too easy.

Usage (from the project root, with .venv activated):
    python src/train_classifier.py
"""
import argparse
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def load_sequences(path):
    data = np.load(path)
    return data["X"], data["y"], data["video"], list(data["classes"])


def split_by_video(y, videos, n_splits=3, seed=SEED):
    """Yield (train, test) index arrays; each video is entirely on one side.

    With n_splits=3 each test part holds about a third of the videos (~70/30).
    """
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    yield from splitter.split(np.zeros(len(y)), y, groups=videos)


def summary_features(X):
    """(sequences, frames, n) -> (sequences, 4n): mean, std, min, max over the frames."""
    return np.concatenate([X.mean(axis=1), X.std(axis=1), X.min(axis=1), X.max(axis=1)],
                          axis=1)


def make_model():
    return RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                  random_state=SEED, n_jobs=-1)


def main():
    parser = argparse.ArgumentParser(description="Train the baseline exercise classifier")
    parser.add_argument("--data", type=Path, default=PROJECT_ROOT / "data" / "sequences.npz")
    parser.add_argument("--output", type=Path,
                        default=PROJECT_ROOT / "models" / "exercise_classifier_rf.joblib")
    args = parser.parse_args()

    X, y, videos, classes = load_sequences(args.data)
    features = summary_features(X)
    splits = list(split_by_video(y, videos))

    # Main result: the first split (~70% of videos for training, ~30% for testing).
    train, test = splits[0]
    model = make_model().fit(features[train], y[train])
    predicted = model.predict(features[test])

    print(f"Train: {len(set(videos[train]))} videos, {len(train)} sequences")
    print(f"Test:  {len(set(videos[test]))} videos, {len(test)} sequences\n")
    print(f"Test accuracy: {accuracy_score(y[test], predicted):.1%}\n")
    print(classification_report(y[test], predicted, target_names=classes, digits=3))
    print("Confusion matrix (rows = true exercise, columns = predicted):")
    print(f"{'':8s}" + "".join(f"{name:>8s}" for name in classes))
    for name, row in zip(classes, confusion_matrix(y[test], predicted)):
        print(f"{name:8s}" + "".join(f"{count:8d}" for count in row))

    # Cross-check: one test split of ~45 videos is small, so repeat with each third of the
    # videos as the test set and look at the spread.
    scores = []
    for fold_train, fold_test in splits:
        fold_model = make_model().fit(features[fold_train], y[fold_train])
        scores.append(accuracy_score(y[fold_test], fold_model.predict(features[fold_test])))
    print(f"\nAccuracy on each of the {len(splits)} video splits: "
          + ", ".join(f"{s:.1%}" for s in scores)
          + f"  (mean {np.mean(scores):.1%})")

    # Final model: trained on all videos, saved for later use.
    final = make_model().fit(features, y)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final, "classes": classes}, args.output)
    print(f"Saved model trained on all videos to {args.output}")


if __name__ == "__main__":
    main()
