from typing import Literal

from pydantic import BaseModel

from .sentinel import ComponentObservation


class ScreeningComponent(ComponentObservation):
    percentage_change: float | None
    early_slope: float | None
    lot_evidence: str | None
    robust_z_score: float | str | None
    candidate: bool | None
    reasons: list[str]
    issue: str | None
    conventional_flag: bool | None


class PopulationSummary(BaseModel):
    total: int
    lots: int
    screened: int
    unassessed: int
    candidates: int
    no_screening_signal: int
    significant_drift: int
    high_side_lot: int


class LotSummary(BaseModel):
    lot_id: str
    total: int
    screened: int
    candidates: int
    unassessed: int


class HistogramBin(BaseModel):
    lower: float
    upper: float
    count: int


class Comparison(BaseModel):
    status: Literal['unconfigured', 'configured']
    limit_ua: float | None
    rule: str
    comparable: int
    excluded: int
    conventional_only: int | None
    sentinel_only: int | None
    both: int | None
    neither: int | None


class PopulationResponse(BaseModel):
    dataset_id: str
    snapshot_id: str
    method: str
    early_drift_threshold_percent: float
    summary: PopulationSummary
    comparison: Comparison
    lots: list[LotSummary]
    drift_histogram: list[HistogramBin]
    components: list[ScreeningComponent]
