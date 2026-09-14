import pandas as pd

from ml.drift.predictor import predict_168h


def test_drift_predictor():
    dataframe = pd.DataFrame(
        [
            {
                "leakage_0h": 10.0,
                "leakage_24h": 10.8,
            }
        ]
    )

    predictions, uncertainty = predict_168h(
        dataframe,
    )

    assert len(predictions) == 1
    assert len(uncertainty) == 1

    assert predictions[0] > 0
    assert uncertainty[0] >= 0