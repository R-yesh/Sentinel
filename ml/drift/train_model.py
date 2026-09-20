import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from ml.features.drift_features import build_drift_features


RANDOM_STATE = 42
DANGEROUS_ERROR_THRESHOLD = 2.0

MODEL_PATH = "ml/drift/random_forest_model.joblib"


def main():
    dataframe = pd.read_csv(
        "data/synthetic/burnin_dataset.csv"
    )

    X = build_drift_features(dataframe)
    y = dataframe["leakage_168h"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    random_forest = RandomForestRegressor(
        n_estimators=200,
        random_state=RANDOM_STATE,
    )

    random_forest.fit(
        X_train,
        y_train,
    )

    joblib.dump(
        random_forest,
        MODEL_PATH,
    )

    rf_predictions = random_forest.predict(
        X_test,
    )

    tree_predictions = np.array(
        [
            tree.predict(X_test.to_numpy())
            for tree in random_forest.estimators_
        ]
    )

    rf_uncertainty = tree_predictions.std(
        axis=0,
    )

    rf_results = dataframe.loc[
        X_test.index,
        [
            "component_id",
            "defect_type",
            "leakage_168h",
        ],
    ].copy()

    rf_results["predicted_168h"] = rf_predictions
    rf_results["uncertainty"] = rf_uncertainty

    rf_results["prediction_error"] = (
        rf_results["leakage_168h"]
        - rf_results["predicted_168h"]
    )

    rf_results["absolute_error"] = (
        rf_results["prediction_error"].abs()
    )

    rf_results["dangerous_underprediction"] = (
        rf_results["prediction_error"]
        > DANGEROUS_ERROR_THRESHOLD
    )

    rf_mae = mean_absolute_error(
        y_test,
        rf_predictions,
    )

    rf_mae_by_type = (
        rf_results
        .groupby("defect_type")["absolute_error"]
        .mean()
        .sort_values()
    )

    underprediction_rate = (
        rf_results["prediction_error"] > 0
    ).mean()

    dangerous_underprediction_rate = (
        rf_results["dangerous_underprediction"].mean()
    )

    dangerous_by_type = (
        rf_results
        .groupby("defect_type")[
            "dangerous_underprediction"
        ]
        .mean()
        .sort_values(
            ascending=False
        )
    )

    latent_mask = (
        rf_results["defect_type"]
        == "latent_defect"
    )

    latent_dangerous_underprediction_rate = (
        rf_results.loc[
            latent_mask,
            "dangerous_underprediction",
        ].mean()
    )

    error_uncertainty_correlation = (
        rf_results["absolute_error"]
        .corr(
            rf_results["uncertainty"]
        )
    )

    print(f"Training components: {len(X_train)}")
    print(f"Testing components: {len(X_test)}")

    print(
        f"Random Forest MAE: "
        f"{rf_mae:.3f} uA"
    )

    print(
        "\nRandom Forest MAE by defect type:"
    )
    print(rf_mae_by_type)

    print(
        "\nUnderprediction rate:"
    )
    print(
        f"{underprediction_rate:.1%}"
    )

    print(
        "\nDangerous underprediction rate "
        f"(>{DANGEROUS_ERROR_THRESHOLD:.1f} uA):"
    )

    print(
        f"{dangerous_underprediction_rate:.1%}"
    )

    print(
        "\nDangerous underprediction rate "
        "by defect type:"
    )

    print(
        dangerous_by_type
    )

    print(
        "\nLatent-defect dangerous "
        "underprediction rate:"
    )

    print(
        f"{latent_dangerous_underprediction_rate:.1%}"
    )

    print(
        "\nCorrelation between "
        "absolute error and uncertainty:"
    )

    print(
        f"{error_uncertainty_correlation:.3f}"
    )

    print(
        f"\nModel saved to: "
        f"{MODEL_PATH}"
    )


if __name__ == "__main__":
    main()