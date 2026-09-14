import joblib
import numpy as np
import pandas as pd

from ml.features.drift_features import build_drift_features


MODEL_PATH = "ml/drift/random_forest_model.joblib"


def load_model():
    return joblib.load(
        MODEL_PATH,
    )


def predict_168h(
    dataframe: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    model = load_model()

    features = build_drift_features(
        dataframe,
    )

    predictions = model.predict(
        features,
    )

    tree_predictions = np.array(
        [
            tree.predict(features.to_numpy())
            for tree in model.estimators_
        ]
    )

    uncertainty = tree_predictions.std(
        axis=0,
    )

    return predictions, uncertainty