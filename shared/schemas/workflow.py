from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from shared.schemas.findings import Finding
from shared.schemas.lot import LotContext


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowState(BaseModel):
    workflow_id: str
    component_id: str
    lot_id: str | None = None

    status: WorkflowStatus = WorkflowStatus.PENDING

    raw_data: dict[str, Any] = Field(default_factory=dict)

    lot_context: LotContext | None = None

    findings: list[Finding] = Field(default_factory=list)

    agent_outputs: dict[str, Any] = Field(default_factory=dict)

    final_decision: str | None = None
    explanation: str | None = None