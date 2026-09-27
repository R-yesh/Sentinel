from pathlib import Path

import pandas as pd

from ml.anomaly.detector import detect_lot_anomaly
from ml.anomaly.isolation_forest import (
    build_early_feature_vector,
    detect_isolation_anomaly,
)


DATASET_PATH = Path(
    "data/synthetic/burnin_dataset.csv"
)


def main():
    dataset = pd.read_csv(DATASET_PATH)

    results = []

    for _, component in dataset.iterrows():
        lot_id = component["lot_id"]

        lot = dataset[
            dataset["lot_id"] == lot_id
        ]

        peers = lot[
            lot["component_id"]
            != component["component_id"]
        ]

        # -------------------------
        # Robust-Z
        # -------------------------

        robust_result = detect_lot_anomaly(
            value=float(
                component["leakage_24h"]
            ),
            population=(
                peers["leakage_24h"]
                .astype(float)
                .tolist()
            ),
        )

        # -------------------------
        # Isolation Forest
        # -------------------------

        component_features = (
            build_early_feature_vector(
                leakage_0h=float(
                    component["leakage_0h"]
                ),
                leakage_24h=float(
                    component["leakage_24h"]
                ),
            )
        )

        peer_features = [
            build_early_feature_vector(
                leakage_0h=float(
                    peer["leakage_0h"]
                ),
                leakage_24h=float(
                    peer["leakage_24h"]
                ),
            )
            for _, peer in peers.iterrows()
        ]

        isolation_result = (
            detect_isolation_anomaly(
                component_features=component_features,
                peer_features=peer_features,
            )
        )

        robust_z = float(
            robust_result.robust_z_score
        )

        isolation_score = float(
            isolation_result.anomaly_score
        )

        isolation_anomaly = bool(
            isolation_result.is_anomaly
        )

        # Reliability concern is primarily
        # high-side leakage deviation.
        robust_elevated = robust_z >= 1.5
        robust_strong = robust_z >= 2.5
        robust_outlier = robust_z >= 3.5

        results.append(
            {
                "component_id": (
                    component["component_id"]
                ),
                "lot_id": lot_id,
                "defect_type": (
                    component["defect_type"]
                ),
                "robust_z_score": robust_z,
                "robust_elevated": (
                    robust_elevated
                ),
                "robust_strong": (
                    robust_strong
                ),
                "robust_outlier": (
                    robust_outlier
                ),
                "isolation_score": (
                    isolation_score
                ),
                "isolation_anomaly": (
                    isolation_anomaly
                ),
            }
        )

    results_df = pd.DataFrame(results)

    # ==================================================
    # Isolation Forest anomaly rates
    # ==================================================

    print(
        "\n=== Isolation Forest "
        "Anomaly Rate by Defect Type (%) ==="
    )

    print(
        (
            results_df
            .groupby("defect_type")[
                "isolation_anomaly"
            ]
            .mean()
            * 100
        )
        .round(1)
        .sort_values()
    )

    # ==================================================
    # Isolation score distributions
    # ==================================================

    print(
        "\n=== Isolation Score Statistics "
        "by Defect Type ==="
    )

    print(
        results_df
        .groupby("defect_type")[
            "isolation_score"
        ]
        .agg(
            [
                "mean",
                "median",
                "min",
                "max",
            ]
        )
        .round(4)
    )

    # ==================================================
    # Robust-Z thresholds
    # ==================================================

    print(
        "\n=== Positive Robust-Z "
        "Detection Rates (%) ==="
    )

    for column, threshold in [
        ("robust_elevated", 1.5),
        ("robust_strong", 2.5),
        ("robust_outlier", 3.5),
    ]:
        print(
            f"\nThreshold >= {threshold}:"
        )

        print(
            (
                results_df
                .groupby("defect_type")[
                    column
                ]
                .mean()
                * 100
            )
            .round(1)
        )

    # ==================================================
    # Detector overlap
    # ==================================================

    results_df["both_detect"] = (
        results_df["robust_elevated"]
        & results_df["isolation_anomaly"]
    )

    results_df["robust_only"] = (
        results_df["robust_elevated"]
        & ~results_df["isolation_anomaly"]
    )

    results_df["isolation_only"] = (
        ~results_df["robust_elevated"]
        & results_df["isolation_anomaly"]
    )

    results_df["neither"] = (
        ~results_df["robust_elevated"]
        & ~results_df["isolation_anomaly"]
    )

    print(
        "\n=== Detector Agreement "
        "(using Robust-Z >= 1.5) (%) ==="
    )

    agreement = (
        results_df
        .groupby("defect_type")[
            [
                "both_detect",
                "robust_only",
                "isolation_only",
                "neither",
            ]
        ]
        .mean()
        * 100
    )

    print(
        agreement.round(1)
    )

    # ==================================================
    # Most Isolation-Forest-anomalous components
    # ==================================================

    print(
        "\n=== 15 Most Isolation-Forest "
        "Anomalous Components ==="
    )

    print(
        results_df
        .sort_values(
            "isolation_score",
            ascending=False,
        )
        .head(15)[
            [
                "component_id",
                "lot_id",
                "defect_type",
                "robust_z_score",
                "isolation_score",
                "isolation_anomaly",
            ]
        ]
        .to_string(
            index=False
        )
    )

    results_df.to_csv(
        "data/synthetic/lot_anomaly_evaluation.csv",
        index=False,
    )


if __name__ == "__main__":
    main()