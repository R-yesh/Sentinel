from pathlib import Path

import pandas as pd

from ml.anomaly.detector import detect_lot_anomaly
from shared.context.lot_context import build_lot_context


DATASET_PATH = Path(
    "data/synthetic/burnin_dataset.csv"
)


def main():
    dataset = pd.read_csv(DATASET_PATH)

    records = []

    for _, row in dataset.iterrows():
        component_id = row["component_id"]

        lot_context = build_lot_context(
            dataset=dataset,
            component_id=component_id,
        )

        result = detect_lot_anomaly(
            value=row["leakage_24h"],
            population=(
                lot_context.leakage_24h_population
            ),
        )

        records.append(
            {
                "component_id": component_id,
                "lot_id": row["lot_id"],
                "defect_type": row["defect_type"],
                "leakage_24h": row["leakage_24h"],
                "robust_z_score": float(
                    result.robust_z_score
                ),
                "percentile": float(
                    result.percentile
                ),
                "anomaly_score": float(
                    result.anomaly_score
                ),
                "is_outlier": bool(
                    result.is_outlier
                ),
            }
        )

    results = pd.DataFrame(records)

    # --------------------------------------------------
    # Overall outlier count
    # --------------------------------------------------

    print("\n=== Overall Lot Outlier Counts ===")

    print(
        results["is_outlier"]
        .value_counts()
        .to_string()
    )

    print(
        "\nOverall outlier rate:"
        f" {results['is_outlier'].mean() * 100:.2f}%"
    )

    # --------------------------------------------------
    # Outlier rate by defect type
    # --------------------------------------------------

    print(
        "\n=== Lot Outlier Rate by Defect Type (%) ==="
    )

    outlier_rates = (
        results
        .groupby("defect_type")["is_outlier"]
        .mean()
        .mul(100)
        .round(2)
        .sort_values(ascending=False)
    )

    print(
        outlier_rates.to_string()
    )

    # --------------------------------------------------
    # Robust z-score statistics
    # --------------------------------------------------

    print(
        "\n=== Robust Z-Score Statistics "
        "by Defect Type ==="
    )

    z_stats = (
        results
        .groupby("defect_type")[
            "robust_z_score"
        ]
        .agg(
            [
                "mean",
                "median",
                "min",
                "max",
            ]
        )
        .round(3)
    )

    print(
        z_stats.to_string()
    )

    # --------------------------------------------------
    # Anomaly score statistics
    # --------------------------------------------------

    print(
        "\n=== Anomaly Score Statistics "
        "by Defect Type ==="
    )

    anomaly_stats = (
        results
        .groupby("defect_type")[
            "anomaly_score"
        ]
        .agg(
            [
                "mean",
                "median",
                "min",
                "max",
            ]
        )
        .round(3)
    )

    print(
        anomaly_stats.to_string()
    )

    # --------------------------------------------------
    # Most statistically unusual components
    # --------------------------------------------------

    ranked = results.copy()

    ranked["abs_robust_z"] = (
        ranked["robust_z_score"].abs()
    )

    most_anomalous = (
        ranked
        .sort_values(
            "abs_robust_z",
            ascending=False,
        )
        .head(15)
    )

    print(
        "\n=== 15 Most Lot-Anomalous Components ==="
    )

    print(
        most_anomalous[
            [
                "component_id",
                "lot_id",
                "defect_type",
                "leakage_24h",
                "robust_z_score",
                "percentile",
                "anomaly_score",
                "is_outlier",
            ]
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------
    # Per-lot outlier counts
    # --------------------------------------------------

    print(
        "\n=== Outliers by Manufacturing Lot ==="
    )

    lot_summary = (
        results
        .groupby("lot_id")
        .agg(
            components=(
                "component_id",
                "count",
            ),
            outliers=(
                "is_outlier",
                "sum",
            ),
            outlier_rate=(
                "is_outlier",
                "mean",
            ),
        )
    )

    lot_summary["outlier_rate"] = (
        lot_summary["outlier_rate"]
        .mul(100)
        .round(2)
    )

    print(
        lot_summary.to_string()
    )
    
    print(
        "\n=== Positive Robust-Z Detection Rates (%) ==="
    )

    for threshold in [
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
        3.5,
    ]:
        detected = (
            results["robust_z_score"]
            >= threshold
        )

        rates = (
            results
            .assign(detected=detected)
            .groupby("defect_type")[
                "detected"
            ]
            .mean()
            .mul(100)
            .round(1)
        )

        print(
            f"\nThreshold >= {threshold}:"
        )

        print(rates.to_string())


if __name__ == "__main__":
    main()