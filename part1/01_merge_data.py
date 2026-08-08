import glob
import os

import pandas as pd

RAW_DIR = os.path.join("..", "Raw_Dataset")
OUT_DIR = os.path.join("..", "Merge_Datasets")
os.makedirs(OUT_DIR, exist_ok=True)


def load_and_tag() -> pd.DataFrame:
    frames = []
    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.csv"))):
        sub_category = os.path.basename(path).replace("products_", "").replace(".csv", "")
        df = pd.read_csv(path)
        df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
        df["sub_category"] = sub_category
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main():
    df = load_and_tag()
    out_path = os.path.join(OUT_DIR, "merged_raw.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved merged (raw, uncleaned) dataset -> {out_path}  (shape={df.shape})")
    print("\nRows per sub_category:")
    print(df["sub_category"].value_counts())


if __name__ == "__main__":
    main()
