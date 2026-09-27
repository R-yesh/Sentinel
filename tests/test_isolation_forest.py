from ml.anomaly.isolation_forest import (
    build_early_feature_vector,
    detect_isolation_anomaly,
)


def test_normal_component():
    peer_features = [
        build_early_feature_vector(10.0, 10.1),
        build_early_feature_vector(10.2, 10.3),
        build_early_feature_vector(9.9, 10.0),
        build_early_feature_vector(10.1, 10.2),
        build_early_feature_vector(9.8, 9.9),
        build_early_feature_vector(10.3, 10.4),
    ]

    component = build_early_feature_vector(
        10.0,
        10.1,
    )

    result = detect_isolation_anomaly(
        component_features=component,
        peer_features=peer_features,
    )

    print("\nNormal:", result)

    assert isinstance(
        result.anomaly_score,
        float,
    )


def test_abnormal_component():
    peer_features = [
        build_early_feature_vector(10.0, 10.1),
        build_early_feature_vector(10.2, 10.3),
        build_early_feature_vector(9.9, 10.0),
        build_early_feature_vector(10.1, 10.2),
        build_early_feature_vector(9.8, 9.9),
        build_early_feature_vector(10.3, 10.4),
    ]

    component = build_early_feature_vector(
        10.0,
        15.0,
    )

    result = detect_isolation_anomaly(
        component_features=component,
        peer_features=peer_features,
    )

    print("\nAbnormal:", result)

    assert isinstance(
        result.anomaly_score,
        float,
    )