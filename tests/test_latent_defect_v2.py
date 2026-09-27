import pytest

from agents.latent_defect.agent import LatentDefectAgent
from shared.schemas.workflow import WorkflowState


def make_state(
    *,
    evidence_level="TYPICAL",
    deviation_direction="TYPICAL",
    robust_z_score=0.0,
    isolation_anomaly=False,
    isolation_score=-0.05,
    percentage_change=1.0,
    early_slope=0.004,
    predicted_168h=10.2,
    prediction_uncertainty=0.5,
):
    state = WorkflowState(
        workflow_id="wf-latent-test",
        component_id="TEST-001",
        raw_data={},
    )

    state.agent_outputs["lot_intelligence"] = {
        "robust_z_score": robust_z_score,
        "robust_anomaly_score": (
            min(abs(robust_z_score) / 5.0, 1.0)
        ),
        "deviation_direction": deviation_direction,
        "evidence_level": evidence_level,
        "isolation_score": isolation_score,
        "isolation_anomaly": isolation_anomaly,
    }

    state.agent_outputs["drift_intelligence"] = {
        "percentage_change": percentage_change,
        "early_slope": early_slope,
        "predicted_168h": predicted_168h,
        "prediction_uncertainty": prediction_uncertainty,
    }

    return state


@pytest.mark.asyncio
async def test_low_concern_when_no_signals_activate():
    state = make_state()

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nLOW CONCERN:")
    print(output)

    assert output["assessment"] == "LOW_CONCERN"
    assert output["signal_count"] == 0
    assert output["signals"] == []


@pytest.mark.asyncio
async def test_elevated_lot_deviation_signal():
    state = make_state(
        evidence_level="ELEVATED",
        deviation_direction="HIGH",
        robust_z_score=1.9,
    )

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nELEVATED LOT DEVIATION:")
    print(output)

    assert output["assessment"] == "ELEVATED_CONCERN"

    assert (
        "elevated_lot_deviation"
        in output["signals"]
    )


@pytest.mark.asyncio
async def test_isolation_anomaly_signal():
    state = make_state(
        isolation_anomaly=True,
        isolation_score=0.08,
    )

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nISOLATION ANOMALY:")
    print(output)

    assert output["assessment"] == "ELEVATED_CONCERN"

    assert (
        "unusual_early_lot_behavior"
        in output["signals"]
    )


@pytest.mark.asyncio
async def test_robust_and_isolation_corroborate():
    state = make_state(
        evidence_level="STRONG_DEVIATION",
        deviation_direction="HIGH",
        robust_z_score=2.8,
        isolation_anomaly=True,
        isolation_score=0.12,
    )

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nCORROBORATED LOT EVIDENCE:")
    print(output)

    assert output["assessment"] == "ELEVATED_CONCERN"

    assert (
        "strong_lot_deviation"
        in output["signals"]
    )

    assert (
        "unusual_early_lot_behavior"
        in output["signals"]
    )


@pytest.mark.asyncio
async def test_high_concern_when_all_major_evidence_agrees():
    state = make_state(
        evidence_level="OUTLIER",
        deviation_direction="HIGH",
        robust_z_score=4.2,
        isolation_anomaly=True,
        isolation_score=0.18,
        percentage_change=15.0,
        early_slope=0.06,
    )

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nHIGH CONCERN:")
    print(output)

    assert output["assessment"] == "HIGH_CONCERN"

    assert (
        "high_side_lot_outlier"
        in output["signals"]
    )

    assert (
        "unusual_early_lot_behavior"
        in output["signals"]
    )

    assert (
        "significant_early_drift"
        in output["signals"]
    )


@pytest.mark.asyncio
async def test_low_side_deviation_not_treated_as_defect_signal():
    state = make_state(
        evidence_level="LOW_SIDE_OUTLIER",
        deviation_direction="LOW",
        robust_z_score=-4.0,
    )

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nLOW-SIDE OUTLIER:")
    print(output)

    assert output["assessment"] == "LOW_CONCERN"

    assert (
        "high_side_lot_outlier"
        not in output["signals"]
    )

    assert (
        "strong_lot_deviation"
        not in output["signals"]
    )

    assert (
        "elevated_lot_deviation"
        not in output["signals"]
    )


@pytest.mark.asyncio
async def test_missing_lot_evidence_returns_insufficient_evidence():
    state = make_state()

    state.agent_outputs["lot_intelligence"].pop(
        "evidence_level"
    )

    agent = LatentDefectAgent()
    result = await agent.run(state)

    output = result.agent_outputs["latent_defect"]

    print("\nMISSING EVIDENCE:")
    print(output)

    assert (
        output["assessment"]
        == "INSUFFICIENT_EVIDENCE"
    )

    assert (
        output["reason"]
        == "insufficient_evidence"
    )

    assert output["signal_count"] == 0