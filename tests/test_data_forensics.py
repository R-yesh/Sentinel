import asyncio

from agents.data_forensics.agent import DataForensicsAgent
from shared.schemas.workflow import WorkflowState


async def main():
    state = WorkflowState(
        workflow_id="wf-001",
        component_id="A173",
        raw_data={
            "leakage_0h": 9.8,
            "leakage_24h": None,
            "leakage_96h": 14.2,
            "leakage_168h": 17.1,
        },
    )

    agent = DataForensicsAgent()

    result = await agent.run(state)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())