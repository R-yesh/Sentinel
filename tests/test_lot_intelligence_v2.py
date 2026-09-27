import asyncio

import pandas as pd

from agents.lot_intelligence.agent import LotIntelligenceAgent
from shared.context.lot_context import build_lot_context
from shared.schemas.workflow import WorkflowState


async def main():
    dataset = pd.read_csv(
        "data/synthetic/burnin_dataset.csv"
    )

    component_id = "C0003"

    component = dataset[
        dataset["component_id"] == component_id
    ].iloc[0]

    lot_context = build_lot_context(
        dataset=dataset,
        component_id=component_id,
    )

    state = WorkflowState(
        workflow_id="wf-lot-v2-test",
        component_id=component_id,
        lot_id=component["lot_id"],
        raw_data={
            "leakage_0h": component["leakage_0h"],
            "leakage_24h": component["leakage_24h"],
        },
        lot_context=lot_context,
    )

    agent = LotIntelligenceAgent()

    result = await agent.run(state)

    print(
        result.agent_outputs[
            "lot_intelligence"
        ]
    )

    print()

    print(
        result.findings[-1].model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    asyncio.run(main())