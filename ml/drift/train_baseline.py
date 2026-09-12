import pandas as pd
import numpy as np

from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from ml.features.drift_features import build_drift_features


RANDOM_STATE = 42


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

    baseline_predictions = X_test["leakage_24h"]

    baseline_mae = mean_absolute_error(
        y_test,
        baseline_predictions,
    )

    model = LinearRegression()

    model.fit(
        X_train,
        y_train,
    )

    ml_predictions = model.predict(
        X_test,
    )

    results = dataframe.loc[
        X_test.index,
        [
            "component_id",
            "defect_type",
            "leakage_168h",
        ],
    ].copy()

    results["predicted_168h"] = ml_predictions

    results["absolute_error"] = (
        results["leakage_168h"]
        - results["predicted_168h"]
    ).abs()

    mae_by_type = (
        results
        .groupby("defect_type")["absolute_error"]
        .mean()
        .sort_values()
    )

    print("\nMAE by defect type:")
    print(mae_by_type)

    worst_predictions = (
        results
        .sort_values(
            "absolute_error",
            ascending=False,
        )
        .head(10)
    )

    print("\nWorst 10 predictions:")
    print(
        worst_predictions[
            [
                "component_id",
                "defect_type",
                "leakage_168h",
                "predicted_168h",
                "absolute_error",
            ]
        ].to_string(index=False)
    )

    ml_mae = mean_absolute_error(
        y_test,
        ml_predictions,
    )

    print(f"Linear Regression MAE: {ml_mae:.3f} uA")

    print(f"Training components: {len(X_train)}")
    print(f"Testing components: {len(X_test)}")
    print(f"Baseline MAE: {baseline_mae:.3f} uA")


    random_forest = RandomForestRegressor(
        n_estimators=200,
        random_state=RANDOM_STATE,
    )

    random_forest.fit(
        X_train,
        y_train,
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

    rf_mae = mean_absolute_error(
        y_test,
        rf_predictions,
    )

    print(
        f"\nRandom Forest MAE: {rf_mae:.3f} uA"
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

    rf_results["absolute_error"] = (
        rf_results["leakage_168h"]
        - rf_results["predicted_168h"]
    ).abs()

    rf_mae_by_type = (
        rf_results
        .groupby("defect_type")["absolute_error"]
        .mean()
        .sort_values()
    )

    print("\nRandom Forest MAE by defect type:")
    print(rf_mae_by_type)

    rf_worst_predictions = (
        rf_results
        .sort_values(
            "absolute_error",
            ascending=False,
        )
        .head(10)
    )

    print("\nRandom Forest worst 10 predictions:")

    print(
        rf_worst_predictions[
            [
                "component_id",
                "defect_type",
                "leakage_168h",
                "predicted_168h",
                "absolute_error",
            ]
        ].to_string(index=False)
    )

    feature_importance = pd.Series(
        random_forest.feature_importances_,
        index=X_train.columns,
    ).sort_values(
        ascending=False,
    )

    most_uncertain = (
        rf_results
        .sort_values(
            "uncertainty",
            ascending=False,
        )
        .head(10)
    )

    print("\nMost uncertain Random Forest predictions:")

    print(
        most_uncertain[
            [
                "component_id",
                "defect_type",
                "leakage_168h",
                "predicted_168h",
                "absolute_error",
                "uncertainty",
            ]
        ].to_string(index=False)
    )

    error_uncertainty_correlation = (
        rf_results["absolute_error"]
        .corr(
            rf_results["uncertainty"]
        )
    )

    print(
        "\nCorrelation between "
        "absolute error and uncertainty:"
    )

    print(
        f"{error_uncertainty_correlation:.3f}"
    )


if __name__ == "__main__":
    main()