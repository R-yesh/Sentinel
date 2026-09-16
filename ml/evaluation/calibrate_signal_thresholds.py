import pandas as pd

from ml.drift.predictor import predict_168h


DANGEROUS_ERROR_THRESHOLD = 2.0


def main():
    dataframe = pd.read_csv(
        "data/synthetic/burnin_dataset.csv"
    )

    predictions, uncertainties = predict_168h(
        dataframe
    )

    dataframe["predicted_168h"] = predictions

    dataframe["prediction_uncertainty"] = (
        uncertainties
    )

    dataframe["percentage_change"] = (
        (
            dataframe["leakage_24h"]
            - dataframe["leakage_0h"]
        )
        / dataframe["leakage_0h"]
        * 100
    )

    dataframe["early_slope"] = (
        dataframe["leakage_24h"]
        - dataframe["leakage_0h"]
    ) / 24

    dataframe["prediction_error"] = (
        dataframe["leakage_168h"]
        - dataframe["predicted_168h"]
    )

    dataframe["dangerous_underprediction"] = (
        dataframe["prediction_error"]
        > DANGEROUS_ERROR_THRESHOLD
    )

    drift_stats = (
        dataframe
        .groupby("defect_type")[
            "percentage_change"
        ]
        .agg(
            [
                "mean",
                "median",
                "min",
                "max",
            ]
        )
    )

    print(
        "\nPercentage change statistics "
        "by defect type:"
    )

    print(
        drift_stats.round(2).to_string()
    )

    slope_stats = (
        dataframe
        .groupby("defect_type")[
            "early_slope"
        ]
        .agg(
            [
                "mean",
                "median",
                "min",
                "max",
            ]
        )
    )

    print(
        "\nEarly slope statistics "
        "by defect type:"
    )

    print(
        slope_stats.round(4).to_string()
    )

    drift_thresholds = [
        2.0,
        4.0,
        6.0,
        8.0,
        10.0,
        12.0,
    ]

    print(
        "\nEarly drift threshold analysis (%):"
    )

    for threshold in drift_thresholds:
        triggered = (
            dataframe["percentage_change"]
            >= threshold
        )

        trigger_rates = (
            dataframe
            .assign(triggered=triggered)
            .groupby("defect_type")["triggered"]
            .mean()
            * 100
        )

        print(
            f"\nThreshold >= {threshold:.1f}%"
        )

        print(
            trigger_rates.round(1).to_string()
        )

    slope_thresholds = [
        0.01,
        0.02,
        0.03,
        0.04,
        0.05,
        0.06,
    ]

    print(
        "\nEarly slope threshold analysis:"
    )

    for threshold in slope_thresholds:
        triggered = (
            dataframe["early_slope"]
            >= threshold
        )

        trigger_rates = (
            dataframe
            .assign(triggered=triggered)
            .groupby("defect_type")["triggered"]
            .mean()
            * 100
        )

        print(
            f"\nThreshold >= "
            f"{threshold:.3f} uA/h"
        )

        print(
            trigger_rates.round(1).to_string()
        )

    uncertainty_thresholds = [
        0.5,
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
    ]

    print(
        "\nPrediction uncertainty "
        "threshold analysis:"
    )

    for threshold in uncertainty_thresholds:
        triggered = (
            dataframe["prediction_uncertainty"]
            >= threshold
        )

        trigger_rates = (
            dataframe
            .assign(triggered=triggered)
            .groupby("defect_type")["triggered"]
            .mean()
            * 100
        )

        print(
            f"\nThreshold >= "
            f"{threshold:.1f} uA"
        )

        print(
            trigger_rates.round(1).to_string()
        )

    dangerous_cases = dataframe[
        dataframe["dangerous_underprediction"]
    ]

    latent_dangerous_cases = dangerous_cases[
        dangerous_cases["defect_type"]
        == "latent_defect"
    ]

    print(
        "\nUncertainty detection of dangerous "
        "underpredictions:"
    )

    for threshold in uncertainty_thresholds:
        dangerous_caught = (
            dangerous_cases[
                "prediction_uncertainty"
            ]
            >= threshold
        ).mean()

        latent_dangerous_caught = (
            latent_dangerous_cases[
                "prediction_uncertainty"
            ]
            >= threshold
        ).mean()

        print(
            f"\nThreshold >= "
            f"{threshold:.1f} uA"
        )

        print(
            "All dangerous underpredictions "
            "caught: "
            f"{dangerous_caught * 100:.1f}%"
        )

        print(
            "Latent dangerous underpredictions "
            "caught: "
            f"{latent_dangerous_caught * 100:.1f}%"
        )


if __name__ == "__main__":
    main()