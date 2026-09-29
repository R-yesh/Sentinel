"""Observational execution data, deliberately separate from WorkflowState."""
from typing import Literal
from pydantic import BaseModel, Field

AgentName = Literal['data_forensics', 'drift_intelligence', 'lot_intelligence',
                    'latent_defect', 'adversarial_qa', 'reliability_judge', 'explanation']
AGENT_NAMES = ('data_forensics', 'drift_intelligence', 'lot_intelligence',
               'latent_defect', 'adversarial_qa', 'reliability_judge', 'explanation')


class AgentExecution(BaseModel):
    agent: AgentName
    status: Literal['completed', 'failed', 'cancelled', 'not_executed']
    started_at: str | None = None
    completed_at: str | None = None
    start_offset_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    end_offset_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    duration_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class WorkflowExecution(BaseModel):
    total_duration_ms: float = Field(ge=0, allow_inf_nan=False)
    agents: list[AgentExecution]
