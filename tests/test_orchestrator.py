import asyncio

from orchestrator.graph.orchestrator import SentinelOrchestrator
from shared.schemas.workflow import WorkflowState


async def main():
    state = WorkflowState(
        workflow_id="wf-004",
        component_id="A173",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": 14.0,
            "lot_leakage_24h": [
                9.8,
                10.2,
                10.1,
                9.9,
                10.4,
                9.7,
                10.0,
            ],
        },
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())