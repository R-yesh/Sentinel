import pandas as pd


FEATURE_COLUMNS = [
    "leakage_0h",
    "leakage_24h",
    "absolute_change_0_24h",
    "percentage_change_0_24h",
    "early_slope",
]


def build_drift_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    features = dataframe[
        [
            "leakage_0h",
            "leakage_24h",
        ]
    ].copy()

    features["absolute_change_0_24h"] = (
        features["leakage_24h"]
        - features["leakage_0h"]
    )

    features["percentage_change_0_24h"] = (
        features["absolute_change_0_24h"]
        / features["leakage_0h"]
        * 100
    )

    features["early_slope"] = (
        features["absolute_change_0_24h"]
        / 24
    )

    return features[FEATURE_COLUMNS]