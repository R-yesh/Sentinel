from ml.anomaly.detector import detect_lot_anomaly


LOT_VALUES = [
    9.8,
    10.2,
    10.1,
    9.9,
    10.4,
    9.7,
    10.0,
]


def test_extreme_value_is_detected_as_outlier():
    result = detect_lot_anomaly(
        value=45.0,
        population=LOT_VALUES,
    )

    assert result.is_outlier is True
    assert result.robust_z_score > 3.5
    assert result.anomaly_score > 0.9


def test_normal_value_is_not_detected_as_outlier():
    result = detect_lot_anomaly(
        value=10.3,
        population=LOT_VALUES,
    )

    assert result.is_outlier is False
    assert abs(result.robust_z_score) < 3.5
    assert result.anomaly_score < 0.9