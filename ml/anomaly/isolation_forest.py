from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass
class IsolationResult:
    anomaly_score: float
    is_anomaly: bool


def build_early_feature_vector(
    leakage_0h: float,
    leakage_24h: float,
) -> list[float]:
    delta = (
        leakage_24h
        - leakage_0h
    )

    if leakage_0h == 0:
        percentage_change = 0.0
    else:
        percentage_change = (
            delta / leakage_0h
        ) * 100.0

    early_slope = delta / 24.0

    return [
        float(leakage_0h),
        float(leakage_24h),
        float(delta),
        float(percentage_change),
        float(early_slope),
    ]


def detect_isolation_anomaly(
    component_features: list[float],
    peer_features: list[list[float]],
) -> IsolationResult:
    if not peer_features:
        raise ValueError(
            "peer_features cannot be empty"
        )

    component_array = np.array(
        component_features,
        dtype=float,
    ).reshape(1, -1)

    peer_array = np.array(
        peer_features,
        dtype=float,
    )

    if peer_array.ndim != 2:
        raise ValueError(
            "peer_features must be a 2D feature matrix"
        )

    if (
        component_array.shape[1]
        != peer_array.shape[1]
    ):
        raise ValueError(
            "component and peer feature dimensions "
            "must match"
        )

    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
    )

    model.fit(peer_array)

    # sklearn's decision_function:
    # positive = more normal
    # negative = more anomalous.
    decision_score = float(
        model.decision_function(
            component_array
        )[0]
    )

    prediction = int(
        model.predict(
            component_array
        )[0]
    )

    # Convert to a more intuitive convention:
    # larger score = more anomalous.
    anomaly_score = -decision_score

    return IsolationResult(
        anomaly_score=anomaly_score,
        is_anomaly=prediction == -1,
    )