"""Copy the videos of our exercises out of the Kaggle "Workout/Exercises Video" zip.

Only the folders we need are extracted (not the whole 4.6 GB archive), into
data/raw_videos/<exercise>/. Videos that are already there are skipped.

Usage (from the project root, with .venv activated):
    python src/copy_dataset.py
    python src/copy_dataset.py --zip path/to/archive.zip
"""
import argparse
import shutil
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ZIP = Path.home() / "Downloads" / "archive.zip"

# folder name in the zip -> our exercise name
FOLDERS = {
    "squat": "squat",
    "push-up": "pushup",
    "barbell biceps curl": "curl",
}


def main():
    parser = argparse.ArgumentParser(description="Copy exercise videos from the dataset zip")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP, help="path to archive.zip")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data" / "raw_videos")
    args = parser.parse_args()

    with zipfile.ZipFile(args.zip) as archive:
        for zip_folder, exercise in FOLDERS.items():
            out_dir = args.output / exercise
            out_dir.mkdir(parents=True, exist_ok=True)
            names = [n for n in archive.namelist()
                     if n.startswith(zip_folder + "/") and not n.endswith("/")]
            copied = 0
            for name in names:
                target = out_dir / Path(name).name
                if target.exists():
                    continue
                with archive.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                copied += 1
            print(f"{exercise:7s}: {len(names)} videos in zip, {copied} copied, "
                  f"{len(names) - copied} already there")


if __name__ == "__main__":
    main()
