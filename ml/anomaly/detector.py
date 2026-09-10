from dataclasses import dataclass
from statistics import median

from ml.anomaly.robust_stats import (
    median_absolute_deviation,
    percentile_rank,
    robust_z_score,
)


@dataclass
class AnomalyResult:
    value: float
    lot_median: float
    lot_mad: float
    robust_z_score: float
    percentile: float
    anomaly_score: float
    is_outlier: bool


def detect_lot_anomaly(
    value: float,
    population: list[float],
) -> AnomalyResult:
    if not population:
        raise ValueError("population cannot be empty")

    lot_median = median(population)
    lot_mad = median_absolute_deviation(population)

    z_score = robust_z_score(
        value=value,
        population=population,
    )

    percentile = percentile_rank(
        value=value,
        population=population,
    )

    if z_score == float("inf"):
        anomaly_score = 1.0
    else:
        anomaly_score = min(
            abs(z_score) / 5.0,
            1.0,
        )

    is_outlier = abs(z_score) >= 3.5

    return AnomalyResult(
        value=value,
        lot_median=lot_median,
        lot_mad=lot_mad,
        robust_z_score=z_score,
        percentile=percentile,
        anomaly_score=anomaly_score,
        is_outlier=is_outlier,
    )