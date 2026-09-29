from typing import Literal
from pydantic import BaseModel
from .population import ScreeningComponent


class Coverage(BaseModel):
    total: int
    evaluated: int
    excluded: int
    flagged: int
    not_flagged: int
    flag_rate: float | None


class TypeCoverage(Coverage):
    defect_type: str


class EvaluationSummary(BaseModel):
    total: int
    evaluated: int
    excluded: int
    unknown_labels: int
    candidates: int
    screening_rate: float | None
    healthy: Coverage
    defective: Coverage


class SignalOverlap(BaseModel):
    drift_only: int
    lot_only: int
    both: int
    neither: int


class EvaluationComparison(BaseModel):
    status: Literal['configured', 'unconfigured']
    limit_ua: float | None
    rule: str
    comparable_defective: int
    excluded_defective: int
    conventional_flagged: int | None
    sentinel_flagged: int | None
    conventional_only: int | None
    sentinel_only: int | None
    both: int | None
    neither: int | None


class Hindsight(BaseModel):
    defect_type: str | None
    synthetic_class: Literal['healthy', 'defective', 'unknown']
    leakage_96h: float | None
    leakage_168h: float | None


class EvaluationComponent(BaseModel):
    early: ScreeningComponent
    hindsight: Hindsight
    evaluated: bool
    comparison_bucket: Literal['conventional_only', 'sentinel_only', 'both', 'neither'] | None


class EvaluationResponse(BaseModel):
    dataset_id: str
    evaluation_only: Literal[True]
    snapshot_id: str
    screening_method: str
    healthy_label: str
    defective_labels: list[str]
    summary: EvaluationSummary
    by_defect_type: list[TypeCoverage]
    signal_overlap: SignalOverlap
    comparison: EvaluationComparison
    components: list[EvaluationComponent]
