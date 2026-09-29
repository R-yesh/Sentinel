from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from shared.schemas.execution import WorkflowExecution


class ComponentObservation(BaseModel):
    component_id: str
    lot_id: str
    leakage_0h: float | None
    leakage_24h: float | None


class ComponentPage(BaseModel):
    dataset_id: str
    items: list[ComponentObservation]
    total: int
    page: int
    page_size: int


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dataset_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)


class InvestigationResponse(BaseModel):
    dataset_id: str
    workflow_execution: WorkflowExecution | None = None
    workflow: dict[str, Any] = Field(
        description=(
            "Serialized WorkflowState. Non-finite numbers are represented by "
            "the strings Infinity, -Infinity, or NaN, including in metadata. "
            "A validation stop may have no final decision or explanation."
        )
    )
