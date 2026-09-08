import asyncio

from agents.drift_intelligence.agent import DriftIntelligenceAgent
from shared.schemas.workflow import WorkflowState


async def main():
    state = WorkflowState(
        workflow_id="wf-003",
        component_id="A173",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": 14.0,
        },
    )

    agent = DriftIntelligenceAgent()

    result = await agent.run(state)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())