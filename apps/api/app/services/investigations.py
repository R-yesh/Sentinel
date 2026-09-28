import asyncio
import math
from uuid import uuid4

from orchestrator.graph.orchestrator import SentinelOrchestrator
from shared.context.lot_context import build_lot_context
from shared.schemas.workflow import WorkflowState

from .datasets import DatasetRepository


class InvalidLotContext(ValueError):
    pass


def json_safe(value):
    """Preserve non-finite analytical values explicitly at the HTTP boundary."""
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def investigate(repository: DatasetRepository, dataset_id: str, component_id: str) -> dict:
    dataset = repository.load(dataset_id)
    component = repository.component(dataset, component_id)
    try:
        lot_context = build_lot_context(dataset, component_id)
    except ValueError as exc:
        raise InvalidLotContext(str(exc)) from exc
    state = WorkflowState(
        workflow_id=str(uuid4()),
        component_id=component_id,
        lot_id=component["lot_id"],
        raw_data={
            "leakage_0h": component["leakage_0h"],
            "leakage_24h": component["leakage_24h"],
        },
        lot_context=lot_context,
    )
    # Called from a synchronous FastAPI route (thread pool), not its event loop.
    result = asyncio.run(SentinelOrchestrator().run(state))
    return {"dataset_id": dataset_id, "workflow": json_safe(result.model_dump())}
