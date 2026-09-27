from dataclasses import dataclass
from enum import Enum
from statistics import median

from ml.anomaly.robust_stats import (
    median_absolute_deviation,
    percentile_rank,
    robust_z_score,
)


class DeviationDirection(str, Enum):
    LOW = "LOW"
    TYPICAL = "TYPICAL"
    HIGH = "HIGH"


class LotEvidenceLevel(str, Enum):
    TYPICAL = "TYPICAL"
    ELEVATED = "ELEVATED"
    STRONG_DEVIATION = "STRONG_DEVIATION"
    OUTLIER = "OUTLIER"
    LOW_SIDE_DEVIATION = "LOW_SIDE_DEVIATION"
    LOW_SIDE_OUTLIER = "LOW_SIDE_OUTLIER"


@dataclass
class AnomalyResult:
    value: float
    lot_median: float
    lot_mad: float
    robust_z_score: float
    percentile: float
    anomaly_score: float

    deviation_direction: DeviationDirection
    evidence_level: LotEvidenceLevel

    is_outlier: bool


def classify_deviation_direction(
    z_score: float,
) -> DeviationDirection:
    if z_score > 0:
        return DeviationDirection.HIGH

    if z_score < 0:
        return DeviationDirection.LOW

    return DeviationDirection.TYPICAL


def classify_evidence_level(
    z_score: float,
) -> LotEvidenceLevel:
    # High-side leakage evidence is reliability-relevant.
    if z_score >= 3.5:
        return LotEvidenceLevel.OUTLIER

    if z_score >= 2.5:
        return LotEvidenceLevel.STRONG_DEVIATION

    if z_score >= 1.5:
        return LotEvidenceLevel.ELEVATED

    # Low-side deviations are statistically interesting,
    # but should not be treated as elevated-leakage evidence.
    if z_score <= -3.5:
        return LotEvidenceLevel.LOW_SIDE_OUTLIER

    if z_score <= -1.5:
        return LotEvidenceLevel.LOW_SIDE_DEVIATION

    return LotEvidenceLevel.TYPICAL


def detect_lot_anomaly(
    value: float,
    population: list[float],
) -> AnomalyResult:
    if not population:
        raise ValueError(
            "population cannot be empty"
        )

    lot_median = median(population)

    lot_mad = median_absolute_deviation(
        population
    )

    z_score = robust_z_score(
        value=value,
        population=population,
    )

    percentile = percentile_rank(
        value=value,
        population=population,
    )

    if abs(z_score) == float("inf"):
        anomaly_score = 1.0
    else:
        anomaly_score = min(
            abs(z_score) / 5.0,
            1.0,
        )

    deviation_direction = (
        classify_deviation_direction(
            z_score
        )
    )

    evidence_level = classify_evidence_level(
        z_score
    )

    # Preserve the strict statistical meaning:
    # an extreme deviation in either direction.
    is_outlier = abs(z_score) >= 3.5

    return AnomalyResult(
        value=float(value),
        lot_median=float(lot_median),
        lot_mad=float(lot_mad),
        robust_z_score=float(z_score),
        percentile=float(percentile),
        anomaly_score=float(anomaly_score),
        deviation_direction=deviation_direction,
        evidence_level=evidence_level,
        is_outlier=bool(is_outlier),
    )