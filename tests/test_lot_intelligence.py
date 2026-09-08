import asyncio

from agents.lot_intelligence.agent import LotIntelligenceAgent
from shared.schemas.workflow import WorkflowState


async def main():
    state = WorkflowState(
        workflow_id="wf-002",
        component_id="A173",
        raw_data={
            "leakage_24h": 45.0,
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

    agent = LotIntelligenceAgent()

    result = await agent.run(state)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())