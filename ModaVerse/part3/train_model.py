"""
Part 3: Predictive Analysis

Reads the cleaned dataset from Part 1, builds TWO regression models to predict
quantity_sold - RandomForestRegressor and XGBoostRegressor - evaluates each
(RMSE, R2), and compares feature importance between them (including whether
sub_category is a top predictor for either model).

Run: python train_model.py   (from inside part3_predictive_model/, venv activated)
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

DATA_PATH = os.path.join("..", "Merge_Datasets", "merged_products.csv")
FIG_DIR = "figures"
OUT_DIR = "output"
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "price",
    "original_price",
    "discount_rate",
    "rating_average",
    "review_counts",
    "favorite_count",
    "number_of_images",
    "vnd_cashback",
    "date_created",
]
BOOL_FEATURES = ["pay_later", "has_video", "is_branded"]
CATEGORICAL_FEATURES = ["sub_category", "fulfillment_type"]
TARGET = "quantity_sold"

MODEL_COLORS = {"random_forest": "#2a78d6", "xgboost": "#eb6834"}


def build_feature_matrix(df: pd.DataFrame):
    X = df[NUMERIC_FEATURES + BOOL_FEATURES].copy()
    for col in BOOL_FEATURES:
        X[col] = X[col].astype(int)

    # One-hot encode categoricals; keep a map back to the parent feature so we
    # can answer "is sub_category, as a whole, a top predictor?" later.
    dummies = pd.get_dummies(df[CATEGORICAL_FEATURES], prefix=CATEGORICAL_FEATURES)
    parent_of = {}
    for col in dummies.columns:
        for parent in CATEGORICAL_FEATURES:
            if col.startswith(parent + "_"):
                parent_of[col] = parent
                break

    X = pd.concat([X, dummies], axis=1)
    y = df[TARGET].astype(float)
    return X, y, parent_of


def aggregate_importance(model, feature_names, parent_of):
    importances = pd.Series(model.feature_importances_, index=feature_names)
    agg = {}
    for feat, imp in importances.items():
        parent = parent_of.get(feat, feat)
        agg[parent] = agg.get(parent, 0.0) + float(imp)
    return importances.sort_values(ascending=False), pd.Series(agg).sort_values(ascending=False)


def train_and_evaluate(name, model, X_train, X_test, y_train, y_test, parent_of):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    raw_imp, agg_imp = aggregate_importance(model, X_train.columns, parent_of)
    raw_imp.to_csv(os.path.join(OUT_DIR, f"feature_importance_raw_onehot_{name}.csv"), header=["importance"])
    agg_imp.to_csv(os.path.join(OUT_DIR, f"feature_importance_aggregated_{name}.csv"), header=["importance"])

    print(f"\n=== {name} ===")
    print(f"RMSE: {rmse:.2f}  |  R2 Score: {r2:.4f}")
    print("Top 5 features:")
    print(agg_imp.head(5))

    return {"name": name, "model": model, "rmse": rmse, "r2": r2, "agg_importance": agg_imp}


def plot_importance_chart(agg_imp, name, color):
    top_n = agg_imp.head(15).sort_values()
    fig, ax = plt.subplots(figsize=(8, 7))
    colors = ["#e34948" if idx == "sub_category" else color for idx in top_n.index]
    ax.barh(top_n.index, top_n.values, color=colors, zorder=3)
    ax.set_xlabel("Feature importance (tổng hợp one-hot theo biến gốc)")
    ax.set_title(f"Top 15 yếu tố quan trọng nhất - {name}\n(đỏ = sub_category)",
                 fontsize=11, weight="bold")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", color="#e1e0d9", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, f"feature_importance_top15_{name}.png"), dpi=150)
    plt.close(fig)


def plot_model_comparison(results):
    names = [r["name"] for r in results]
    colors = [MODEL_COLORS[n] for n in names]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    rmses = [r["rmse"] for r in results]
    bars = axes[0].bar(names, rmses, color=colors, width=0.5, zorder=3)
    for b, v in zip(bars, rmses):
        axes[0].text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=10)
    axes[0].set_title("RMSE (thấp hơn = tốt hơn)", fontsize=10, weight="bold")
    axes[0].grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)

    r2s = [r["r2"] for r in results]
    bars = axes[1].bar(names, r2s, color=colors, width=0.5, zorder=3)
    for b, v in zip(bars, r2s):
        axes[1].text(b.get_x() + b.get_width() / 2, v, f"{v:.3f}", ha="center", va="bottom", fontsize=10)
    axes[1].set_title("R2 Score (cao hơn = tốt hơn)", fontsize=10, weight="bold")
    axes[1].grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)

    for ax in axes:
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.set_axisbelow(True)

    fig.suptitle("So sánh Random Forest vs. XGBoost (test set)", fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "model_comparison_rmse_r2.png"), dpi=150)
    plt.close(fig)

    # side-by-side top-10 feature importance comparison
    top_union = sorted(
        set(results[0]["agg_importance"].head(10).index) | set(results[1]["agg_importance"].head(10).index),
        key=lambda f: -max(
            results[0]["agg_importance"].get(f, 0), results[1]["agg_importance"].get(f, 0)
        ),
    )[:12]
    y_pos = np.arange(len(top_union))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9, 7))
    for i, r in enumerate(results):
        vals = [r["agg_importance"].get(f, 0) for f in top_union]
        offset = (i - 0.5) * width
        ax.barh(y_pos + offset, vals, height=width, label=r["name"], color=MODEL_COLORS[r["name"]], zorder=3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_union)
    ax.invert_yaxis()
    ax.set_xlabel("Feature importance (tổng hợp one-hot theo biến gốc)")
    ax.set_title("So sánh Feature Importance: Random Forest vs. XGBoost", fontsize=11, weight="bold")
    ax.legend(frameon=False)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", color="#e1e0d9", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "feature_importance_comparison.png"), dpi=150)
    plt.close(fig)


def main():
    df = pd.read_csv(DATA_PATH)
    X, y, parent_of = build_feature_matrix(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    X_train_scaled[NUMERIC_FEATURES] = scaler.fit_transform(X_train[NUMERIC_FEATURES])
    X_test_scaled[NUMERIC_FEATURES] = scaler.transform(X_test[NUMERIC_FEATURES])

    models = {
        "random_forest": RandomForestRegressor(
            n_estimators=300, max_depth=None, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        "xgboost": XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
    }

    results = [
        train_and_evaluate(name, model, X_train_scaled, X_test_scaled, y_train, y_test, parent_of)
        for name, model in models.items()
    ]

    with open(os.path.join(OUT_DIR, "model_performance.txt"), "w") as f:
        f.write("=== Part 3: Predictive Analysis - Model Performance ===\n\n")
        f.write(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}\n")
        f.write(f"y_test mean: {y_test.mean():.2f}, y_test std: {y_test.std():.2f}\n\n")
        for r in results:
            f.write(f"--- {r['name']} ---\n")
            f.write(f"RMSE: {r['rmse']:.2f}\n")
            f.write(f"R2 Score: {r['r2']:.4f}\n\n")

    for r in results:
        plot_importance_chart(r["agg_importance"], r["name"], MODEL_COLORS[r["name"]])

    plot_model_comparison(results)

    best = min(results, key=lambda r: r["rmse"])
    print(f"\nBetter model by RMSE: {best['name']} (RMSE={best['rmse']:.2f}, R2={best['r2']:.4f})")

    # --- interpretation notes: compare both models' verdicts ---
    lines = ["=== Part 3: Interpretation notes (Random Forest vs. XGBoost) ===", ""]
    lines.append(f"Better model by RMSE: {best['name']} (RMSE={best['rmse']:.2f}, R2={best['r2']:.4f})")
    lines.append("")
    for r in results:
        agg_imp = r["agg_importance"]
        top5 = agg_imp.head(5)
        sub_cat_rank = list(agg_imp.index).index("sub_category") + 1
        in_top5 = "sub_category" in top5.index
        lines.append(f"--- {r['name']} ---")
        lines.append(f"RMSE={r['rmse']:.2f}, R2={r['r2']:.4f}")
        lines.append(f"Top 5 predictors: {', '.join(top5.index)}")
        lines.append(f"sub_category rank: #{sub_cat_rank} of {len(agg_imp)} "
                     f"(importance={agg_imp['sub_category']:.4f}) - "
                     f"{'IN' if in_top5 else 'NOT in'} top 5")
        lines.append("")

    ranks = {r["name"]: list(r["agg_importance"].index).index("sub_category") + 1 for r in results}
    agree = (ranks["random_forest"] > 5) == (ranks["xgboost"] > 5)
    lines.append(
        "Both models agree sub_category is NOT a top-5 predictor."
        if agree and all(v > 5 for v in ranks.values())
        else "Both models agree sub_category IS a top-5 predictor."
        if agree
        else "Models DISAGREE on whether sub_category is a top-5 predictor - "
             "treat the sub_category conclusion as model-dependent, not settled."
    )
    lines.append(
        "-> If both agree it's not top-5, quantity_sold is driven mainly by product-level "
        "factors (reviews, listing age, price, images) rather than which category a product "
        "sits in - i.e. execution matters more than category choice."
    )
    lines.append("")
    lines.append("CAVEAT on review_counts (typically the #1 feature by a wide margin in both models):")
    lines.append(
        "review_counts can only accumulate AFTER a product has been purchased, so it is "
        "mechanically correlated with quantity_sold rather than a controllable lever a "
        "seller can pull before selling. Treat it as a proxy/leakage-like feature: strong "
        "for prediction, weak for actionable strategy. For business recommendations, the "
        "more actionable levers are the next-ranked features (date_created, price, "
        "number_of_images, discount_rate, has_video, is_branded)."
    )
    lines.append("")
    lines.append(
        f"R2 in the {results[0]['r2']:.2f}-{results[1]['r2']:.2f} range is modest - quantity_sold "
        f"is heavy-tailed (std {y_test.std():.0f} vs mean {y_test.mean():.1f}), a handful of viral "
        "products drive most volume, which caps how well any tabular regression can fit without "
        "log-transforming the target or modeling top-sellers separately."
    )

    with open(os.path.join(OUT_DIR, "interpretation_notes.txt"), "w") as f:
        f.write("\n".join(lines))
    print("\n" + "\n".join(lines))

    print(f"\nSaved model performance -> {OUT_DIR}/model_performance.txt")
    print(f"Saved feature importance tables -> {OUT_DIR}/")
    print(f"Saved figures -> {FIG_DIR}/ "
          f"(feature_importance_top15_<model>.png, model_comparison_rmse_r2.png, "
          f"feature_importance_comparison.png)")


if __name__ == "__main__":
    main()
