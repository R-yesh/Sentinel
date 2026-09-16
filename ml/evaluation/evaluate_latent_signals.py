import pandas as pd

from ml.drift.predictor import predict_168h
from ml.anomaly.detector import detect_lot_anomaly

LOT_ANOMALY_THRESHOLD = 0.7
EARLY_DRIFT_THRESHOLD = 6.0
UNCERTAINTY_THRESHOLD = 1.5

DANGEROUS_ERROR_THRESHOLD = 2.0

def main():
    dataframe = pd.read_csv(
        "data/synthetic/burnin_dataset.csv"
    )

    predictions, uncertainties = predict_168h(dataframe)

    dataframe["predicted_168h"] = predictions
    dataframe["prediction_uncertainty"] = uncertainties

    dataframe["percentage_change"] = (
        (
            dataframe["leakage_24h"]
            - dataframe["leakage_0h"]
        )
        / dataframe["leakage_0h"]
        * 100
    )

    lot_population = (
        dataframe["leakage_24h"]
        .tolist()
    )

    anomaly_scores = []

    for leakage_24h in dataframe["leakage_24h"]:
        result = detect_lot_anomaly(
            leakage_24h,
            lot_population,
        )

        anomaly_scores.append(
            result.anomaly_score
        )

    dataframe["lot_anomaly_score"] = anomaly_scores

    dataframe["strong_lot_anomaly"] = (
        dataframe["lot_anomaly_score"]
        >= LOT_ANOMALY_THRESHOLD
    )

    dataframe["significant_early_drift"] = (
        dataframe["percentage_change"]
        >= EARLY_DRIFT_THRESHOLD
    )

    dataframe["high_prediction_uncertainty"] = (
        dataframe["prediction_uncertainty"]
        >= UNCERTAINTY_THRESHOLD
    )

    dataframe["signal_count"] = (
        dataframe[
            [
                "strong_lot_anomaly",
                "significant_early_drift",
                "high_prediction_uncertainty",
            ]
        ]
        .sum(axis=1)
    )

    signal_summary = (
        dataframe
        .groupby("defect_type")[
            [
                "strong_lot_anomaly",
                "significant_early_drift",
                "high_prediction_uncertainty",
            ]
        ]
        .mean()
        * 100
    )

    print(
        "\nSignal activation rate by defect type (%):"
    )

    print(
        signal_summary.round(1).to_string()
    )

    signal_count_summary = (
        dataframe
        .groupby("defect_type")["signal_count"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
        * 100
    )

    print(
        "\nSignal count distribution by defect type (%):"
    )

    print(
        signal_count_summary.round(1).to_string()
    )

    dataframe["prediction_error"] = (
        dataframe["leakage_168h"]
        - dataframe["predicted_168h"]
    )

    dataframe["dangerous_underprediction"] = (
        dataframe["prediction_error"] > 2.0
    )

    dangerous_cases = dataframe[
        dataframe["dangerous_underprediction"]
    ] 

    caught_by_signals = (
        dangerous_cases["signal_count"] > 0
    ).mean()

    print(
        "\nDangerous underpredictions caught "
        "by at least one Sentinel signal:"
    )

    print(
        f"{caught_by_signals * 100:.1f}%"
    )

    latent_dangerous_cases = dangerous_cases[
        dangerous_cases["defect_type"]
        == "latent_defect"
    ]

    latent_caught_by_signals = (
        latent_dangerous_cases["signal_count"] > 0
    ).mean()

    print(
        "\nLatent-defect dangerous underpredictions "
        "caught by at least one Sentinel signal:"
    )

    print(
        f"{latent_caught_by_signals * 100:.1f}%"
    )


if __name__ == "__main__":
    main()