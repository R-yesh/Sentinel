import math

import pytest

from agents.data_forensics.agent import DataForensicsAgent
from shared.schemas.workflow import WorkflowState


async def run_data_forensics(raw_data):
    state = WorkflowState(
        workflow_id="wf-data-forensics-test",
        component_id="TEST-001",
        raw_data=raw_data,
    )

    agent = DataForensicsAgent()

    return await agent.run(state)


@pytest.mark.asyncio
async def test_valid_measurements_pass():
    result = await run_data_forensics(
        {
            "leakage_0h": 9.8,
            "leakage_24h": 10.2,
        }
    )

    output = result.agent_outputs["data_forensics"]

    assert output["passed"] is True
    assert output["missing_fields"] == []
    assert output["invalid_numeric_fields"] == []
    assert output["physically_invalid_fields"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "raw_data, expected_field",
    [
        (
            {
                "leakage_0h": 9.8,
            },
            "leakage_24h",
        ),
        (
            {
                "leakage_0h": 9.8,
                "leakage_24h": None,
            },
            "leakage_24h",
        ),
    ],
)
async def test_missing_measurements_fail(
    raw_data,
    expected_field,
):
    result = await run_data_forensics(raw_data)

    output = result.agent_outputs["data_forensics"]

    assert output["passed"] is False
    assert expected_field in output["missing_fields"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_value",
    [
        "10.2",
        math.nan,
        math.inf,
        -math.inf,
        True,
    ],
)
async def test_invalid_numeric_measurements_fail(
    invalid_value,
):
    result = await run_data_forensics(
        {
            "leakage_0h": 9.8,
            "leakage_24h": invalid_value,
        }
    )

    output = result.agent_outputs["data_forensics"]

    assert output["passed"] is False
    assert (
        "leakage_24h"
        in output["invalid_numeric_fields"]
    )


@pytest.mark.asyncio
async def test_negative_leakage_fails():
    result = await run_data_forensics(
        {
            "leakage_0h": 9.8,
            "leakage_24h": -3.5,
        }
    )

    output = result.agent_outputs["data_forensics"]

    assert output["passed"] is False
    assert (
        "leakage_24h"
        in output["physically_invalid_fields"]
    )