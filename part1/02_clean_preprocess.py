import os
import pandas as pd

MERGE_DIR = os.path.join("..", "Merge_Datasets")
IN_PATH = os.path.join(MERGE_DIR, "merged_raw.csv")
REPORT_DIR = "output"
os.makedirs(MERGE_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

RENAME_MAP = {
    "review_count": "review_counts",
    "favourite_count": "favorite_count",
}


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    log = []
    df = df.rename(columns=RENAME_MAP)

    log.append(f"Rows loaded (from merged_raw.csv): {len(df)}")

    # --- text columns: strip whitespace, fix stray tabs/newlines ---
    for col in ["name", "description", "brand", "current_seller", "fulfillment_type", "category"]:
        df[col] = df[col].astype(str).str.strip()

    # --- missing values ---
    n_missing_fulfillment = df["fulfillment_type"].isin(["nan", ""]).sum()
    df.loc[df["fulfillment_type"].isin(["nan", ""]), "fulfillment_type"] = "unknown"
    log.append(f"fulfillment_type missing -> filled 'unknown': {n_missing_fulfillment}")

    n_missing_brand = df["brand"].isin(["nan", ""]).sum()
    df.loc[df["brand"].isin(["nan", ""]), "brand"] = "OEM"
    log.append(f"brand missing -> filled 'OEM' (per data dictionary, OEM = no brand): {n_missing_brand}")

    # --- dtype normalization ---
    df["original_price"] = pd.to_numeric(df["original_price"], errors="coerce").fillna(0).astype(float)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(float)
    df["rating_average"] = pd.to_numeric(df["rating_average"], errors="coerce").fillna(0.0).astype(float)
    for col in ["review_counts", "favorite_count", "date_created", "number_of_images", "vnd_cashback", "quantity_sold"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["pay_later", "has_video"]:
        df[col] = df[col].astype(str).str.lower().map({"true": True, "false": False}).fillna(False)

    # original_price should be at least price (some rows may have original_price < price due to data entry)
    bad_price_rows = (df["original_price"] < df["price"]).sum()
    df.loc[df["original_price"] < df["price"], "original_price"] = df["price"]
    log.append(f"original_price < price rows -> original_price raised to price: {bad_price_rows}")

    # --- duplicates ---
    dup_ids = df["id"].duplicated().sum()
    log.append(f"Duplicate product ids across category files (kept, not dropped): {dup_ids}")

    exact_dupes = df.duplicated(subset=["id", "sub_category"]).sum()
    df = df.drop_duplicates(subset=["id", "sub_category"])
    log.append(f"Exact duplicate rows (same id + sub_category) dropped: {exact_dupes}")

    log.append(f"Rows after cleaning: {len(df)}")
    return df, log


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df["discount_rate"] = 0.0
    mask = df["original_price"] > 0
    df.loc[mask, "discount_rate"] = (
        (df.loc[mask, "original_price"] - df.loc[mask, "price"]) / df.loc[mask, "original_price"] * 100
    ).round(2)

    df["is_branded"] = df["brand"].str.upper() != "OEM"

    return df


def main():
    df = pd.read_csv(IN_PATH)
    df, log = clean(df)
    df = engineer_features(df)

    out_path = os.path.join(MERGE_DIR, "merged_products.csv")
    df.to_csv(out_path, index=False)

    report_path = os.path.join(REPORT_DIR, "cleaning_report.txt")
    with open(report_path, "w") as f:
        f.write("=== Part 1.2: Data Cleaning & Preprocessing - Report ===\n\n")
        for line in log:
            f.write(line + "\n")
        f.write("\n--- sub_category row counts ---\n")
        f.write(df["sub_category"].value_counts().to_string())
        f.write("\n\n--- dtypes ---\n")
        f.write(df.dtypes.to_string())
        f.write("\n\n--- discount_rate / is_branded sample stats ---\n")
        f.write(df[["discount_rate"]].describe().to_string())
        f.write("\n\n")
        f.write(df["is_branded"].value_counts().to_string())

    print(f"Saved cleaned & feature-engineered dataset -> {out_path}  (shape={df.shape})")
    print(f"Saved cleaning report -> {report_path}")
    for line in log:
        print(" -", line)


if __name__ == "__main__":
    main()
