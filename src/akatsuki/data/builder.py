"""Dataset builder for AKATSUKI training data."""

import os
import json
import glob


class DatasetBuilder:
    def __init__(self, output_dir="./datasets"):
        self.output_dir = output_dir
        self.records = []

    def add_conversation(self, messages):
        self.records.append({"messages": messages})

    def add_text(self, text):
        self.records.append({"text": text})

    def add_chosen_rejected(self, prompt, chosen, rejected):
        self.records.append({
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
        })

    def from_jsonl(self, path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.records.append(json.loads(line))

    def from_directory(self, dir_path, ext=".txt"):
        for path in sorted(glob.glob(os.path.join(dir_path, f"**/*{ext}"), recursive=True)):
            with open(path, "r", encoding="utf-8") as f:
                self.add_text(f.read())

    def to_jsonl(self, name="dataset"):
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, f"{name}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for record in self.records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Wrote {len(self.records)} records to {path}")
        return path

    def split(self, train_ratio=0.9, name="dataset"):
        os.makedirs(self.output_dir, exist_ok=True)
        split_idx = int(len(self.records) * train_ratio)
        train = self.records[:split_idx]
        val = self.records[split_idx:]

        train_path = os.path.join(self.output_dir, f"{name}_train.jsonl")
        val_path = os.path.join(self.output_dir, f"{name}_val.jsonl")

        for path, records in [(train_path, train), (val_path, val)]:
            with open(path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"Train: {len(train)} records -> {train_path}")
        print(f"Val: {len(val)} records -> {val_path}")
        return train_path, val_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build training dataset")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("--output", "-o", default="./datasets", help="Output directory")
    parser.add_argument("--name", default="dataset", help="Dataset name")
    parser.add_argument("--split", action="store_true", help="Split into train/val")
    args = parser.parse_args()

    builder = DatasetBuilder(output_dir=args.output)

    if os.path.isdir(args.input):
        builder.from_directory(args.input)
    else:
        ext = os.path.splitext(args.input)[1].lower()
        if ext == ".jsonl":
            builder.from_jsonl(args.input)
        else:
            builder.from_directory(os.path.dirname(args.input) or ".", ext=ext or ".txt")

    if args.split:
        builder.split(name=args.name)
    else:
        builder.to_jsonl(name=args.name)


if __name__ == "__main__":
    main()
