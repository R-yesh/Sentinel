import pytest

from orchestrator.graph.orchestrator import SentinelOrchestrator
from shared.schemas.workflow import (
    LotContext,
    WorkflowState,
    WorkflowStatus,
)


def make_lot_context(
    lot_id: str = "LOT-E2E-001",
) -> LotContext:
    """
    Creates deterministic paired 0h and 24h
    measurements for peer components in one lot.

    The component under test is NOT included.

    Pairing matters because Lot Intelligence V2 uses:
    - robust statistics on lot-relative leakage
    - Isolation Forest on early component behaviour
    """

    offsets = [
        -0.80,
        -0.65,
        -0.55,
        -0.48,
        -0.42,
        -0.37,
        -0.32,
        -0.28,
        -0.24,
        -0.20,
        -0.17,
        -0.14,
        -0.11,
        -0.08,
        -0.05,
        -0.03,
        -0.01,
        0.00,
        0.02,
        0.04,
        0.06,
        0.09,
        0.12,
        0.15,
        0.18,
        0.22,
        0.26,
        0.30,
        0.35,
        0.40,
        0.46,
        0.52,
        0.60,
        0.70,
        0.82,
        0.95,
        -0.72,
        -0.58,
        -0.45,
        -0.34,
        -0.25,
        -0.16,
        -0.07,
        0.01,
        0.10,
        0.21,
        0.33,
        0.49,
        0.68,
    ]

    leakage_0h_population = [
        10.0 + offset
        for offset in offsets
    ]

    # Give normal peer components small,
    # realistic early movement.
    leakage_24h_population = [
        value + 0.05
        for value in leakage_0h_population
    ]

    component_ids = [
        f"PEER-{index:03d}"
        for index in range(
            1,
            len(leakage_0h_population) + 1,
        )
    ]

    return LotContext(
        lot_id=lot_id,
        component_ids=component_ids,
        leakage_0h_population=(
            leakage_0h_population
        ),
        leakage_24h_population=(
            leakage_24h_population
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "component_id",
        "leakage_0h",
        "leakage_24h",
        "expected_decision",
    ),
    [
        # -----------------------------------------
        # HEALTHY
        #
        # Stable early behaviour and statistically
        # ordinary relative to its manufacturing lot.
        # -----------------------------------------
        (
            "HEALTHY-E2E-V2",
            10.00,
            10.08,
            "PASS",
        ),

        # -----------------------------------------
        # BORDERLINE / CONFLICTING
        #
        # Meaningful early increase while the
        # absolute 24h value is not nearly as
        # extreme as the severe case.
        # -----------------------------------------
        (
            "BORDERLINE-E2E-V2",
            9.70,
            10.55,
            "REVIEW",
        ),

        # -----------------------------------------
        # SEVERE
        #
        # Massive observed early degradation and
        # extreme high-side lot deviation.
        # -----------------------------------------
        (
            "SEVERE-E2E-V2",
            10.00,
            13.00,
            "REJECT",
        ),
    ],
)
async def test_orchestrator_v2_end_to_end(
    component_id,
    leakage_0h,
    leakage_24h,
    expected_decision,
):
    lot_id = "LOT-E2E-001"

    lot_context = make_lot_context(
        lot_id=lot_id,
    )

    state = WorkflowState(
        workflow_id=f"wf-{component_id}",
        component_id=component_id,
        lot_id=lot_id,
        raw_data={
            "leakage_0h": leakage_0h,
            "leakage_24h": leakage_24h,
        },
        lot_context=lot_context,
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    print()
    print("=" * 70)
    print(component_id)
    print("=" * 70)

    print("\nData Forensics:")
    print(
        result.agent_outputs.get(
            "data_forensics"
        )
    )

    print("\nDrift Intelligence:")
    print(
        result.agent_outputs.get(
            "drift_intelligence"
        )
    )

    print("\nLot Intelligence:")
    print(
        result.agent_outputs.get(
            "lot_intelligence"
        )
    )

    print("\nLatent Defect:")
    print(
        result.agent_outputs.get(
            "latent_defect"
        )
    )

    print("\nAdversarial QA:")
    print(
        result.agent_outputs.get(
            "adversarial_qa"
        )
    )

    print("\nReliability Judge:")
    print(
        result.agent_outputs.get(
            "reliability_judge"
        )
    )

    print("\nExplanation:")
    print(
        result.agent_outputs.get(
            "explanation"
        )
    )

    print(
        f"\nEXPECTED: {expected_decision}"
    )
    print(
        f"ACTUAL:   {result.final_decision}"
    )

    # -----------------------------------------
    # Every agent must actually have executed.
    # -----------------------------------------

    expected_agents = [
        "data_forensics",
        "drift_intelligence",
        "lot_intelligence",
        "latent_defect",
        "adversarial_qa",
        "reliability_judge",
        "explanation",
    ]

    for agent_name in expected_agents:
        assert agent_name in result.agent_outputs

    # -----------------------------------------
    # Data Forensics
    # -----------------------------------------

    data_output = result.agent_outputs[
        "data_forensics"
    ]

    assert data_output["passed"] is True

    # -----------------------------------------
    # Lot Intelligence V2
    # -----------------------------------------

    lot_output = result.agent_outputs[
        "lot_intelligence"
    ]

    # This is important:
    # normal E2E scenarios must actually reach
    # full lot reasoning rather than silently
    # falling through a guardrail.
    assert "reason" not in lot_output

    assert lot_output["lot_id"] == lot_id

    assert (
        lot_output["lot_population_size"]
        == len(
            lot_context.leakage_24h_population
        )
    )

    assert isinstance(
        lot_output["component_value"],
        float,
    )

    assert isinstance(
        lot_output["lot_median"],
        float,
    )

    assert isinstance(
        lot_output["lot_mad"],
        float,
    )

    assert isinstance(
        lot_output["robust_z_score"],
        float,
    )

    assert isinstance(
        lot_output["robust_anomaly_score"],
        float,
    )

    assert lot_output[
        "deviation_direction"
    ] in {
        "LOW",
        "TYPICAL",
        "HIGH",
    }

    assert lot_output[
        "evidence_level"
    ] in {
        "TYPICAL",
        "ELEVATED",
        "STRONG_DEVIATION",
        "OUTLIER",
        "LOW_SIDE_DEVIATION",
        "LOW_SIDE_OUTLIER",
    }

    assert isinstance(
        lot_output["is_outlier"],
        bool,
    )

    assert isinstance(
        lot_output["isolation_score"],
        float,
    )

    assert isinstance(
        lot_output["isolation_anomaly"],
        bool,
    )

    # -----------------------------------------
    # Latent synthesis
    # -----------------------------------------

    latent_output = result.agent_outputs[
        "latent_defect"
    ]

    assert latent_output["assessment"] in {
        "LOW_CONCERN",
        "ELEVATED_CONCERN",
        "HIGH_CONCERN",
    }

    assert (
        latent_output["assessment"]
        != "INSUFFICIENT_EVIDENCE"
    )

    assert isinstance(
        latent_output["signals"],
        list,
    )

    assert isinstance(
        latent_output["signal_count"],
        int,
    )

    # -----------------------------------------
    # Adversarial QA
    # -----------------------------------------

    adversarial_output = result.agent_outputs[
        "adversarial_qa"
    ]

    assert (
        adversarial_output["review"]
        is not None
    )

    # -----------------------------------------
    # Reliability Judge
    # -----------------------------------------

    judge_output = result.agent_outputs[
        "reliability_judge"
    ]

    assert (
        judge_output["decision"]
        == expected_decision
    )

    assert judge_output["reason_code"]

    assert judge_output["reasoning"]

    assert isinstance(
        judge_output["supporting_evidence"],
        list,
    )

    assert isinstance(
        judge_output["unresolved_concerns"],
        list,
    )

    assert (
        result.final_decision
        == expected_decision
    )

    # Normal E2E scenarios must not arrive at
    # REVIEW because evidence disappeared.
    assert (
        judge_output["reason_code"]
        != "INSUFFICIENT_EVIDENCE"
    )

    # -----------------------------------------
    # Workflow status
    # -----------------------------------------

    if expected_decision == "REVIEW":
        assert (
            result.status
            == WorkflowStatus.NEEDS_REVIEW
        )

    else:
        assert (
            result.status
            == WorkflowStatus.COMPLETED
        )

    # -----------------------------------------
    # Explanation
    # -----------------------------------------

    explanation_output = result.agent_outputs[
        "explanation"
    ]

    assert explanation_output["headline"]

    assert explanation_output["summary"]

    assert isinstance(
        explanation_output["key_evidence"],
        list,
    )

    assert explanation_output[
        "decision_reasoning"
    ]

    assert explanation_output[
        "recommended_action"
    ]

    assert result.explanation

    # Explanation must never mutate the
    # Reliability Judge's final decision.
    assert (
        result.final_decision
        == judge_output["decision"]
    )


@pytest.mark.asyncio
async def test_orchestrator_v2_lot_context_guardrail():
    """
    A valid but incorrectly identified lot context
    must not silently enter normal lot-relative
    reasoning.

    Everything except the lot ID is deliberately
    valid so this test isolates the mismatch
    guardrail specifically.
    """

    state = WorkflowState(
        workflow_id="wf-invalid-lot-v2",
        component_id="INVALID-LOT-V2",
        lot_id="LOT-001",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": 10.5,
        },
        lot_context=make_lot_context(
            lot_id="LOT-999",
        ),
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    print()
    print("=" * 70)
    print("LOT CONTEXT GUARDRAIL")
    print("=" * 70)

    print(
        result.agent_outputs.get(
            "lot_intelligence"
        )
    )

    print("\nLatent Defect:")
    print(
        result.agent_outputs.get(
            "latent_defect"
        )
    )

    print("\nReliability Judge:")
    print(
        result.agent_outputs.get(
            "reliability_judge"
        )
    )

    lot_output = result.agent_outputs[
        "lot_intelligence"
    ]

    assert lot_output["passed"] is False

    assert (
        lot_output["reason"]
        == "lot_context_mismatch"
    )

    # Invalid lot evidence must propagate into
    # insufficient combined evidence rather than
    # being used as legitimate lot evidence.
    latent_output = result.agent_outputs[
        "latent_defect"
    ]

    assert (
        latent_output["assessment"]
        == "INSUFFICIENT_EVIDENCE"
    )

    # Invalid lot evidence must never produce an
    # automatic acceptance or rejection.
    judge_output = result.agent_outputs[
        "reliability_judge"
    ]

    assert (
        judge_output["decision"]
        == "REVIEW"
    )

    assert (
        judge_output["reason_code"]
        == "INSUFFICIENT_EVIDENCE"
    )

    assert result.final_decision == "REVIEW"

    assert (
        result.status
        == WorkflowStatus.NEEDS_REVIEW
    )


@pytest.mark.asyncio
async def test_orchestrator_v2_missing_lot_value_guardrail():
    """
    Missing peer measurements must be detected
    by Data Forensics and must stop the reasoning
    pipeline before statistical or ML analysis.
    """

    state = WorkflowState(
        workflow_id="wf-missing-lot-value-v2",
        component_id="MISSING-LOT-VALUE-V2",
        lot_id="LOT-001",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": 10.2,
        },
        lot_context=LotContext(
            lot_id="LOT-001",
            component_ids=[
                "PEER-001",
                "PEER-002",
                "PEER-003",
                "PEER-004",
            ],
            leakage_0h_population=[
                9.8,
                10.0,
                None,
                10.2,
            ],
            leakage_24h_population=[
                9.9,
                10.1,
                10.2,
                10.3,
            ],
        ),
    )

    orchestrator = SentinelOrchestrator()

    result = await orchestrator.run(state)

    print()
    print("=" * 70)
    print("MISSING LOT VALUE GUARDRAIL")
    print("=" * 70)

    print("\nData Forensics:")
    print(
        result.agent_outputs.get(
            "data_forensics"
        )
    )

    data_output = result.agent_outputs[
        "data_forensics"
    ]

    # -----------------------------------------
    # Data Forensics must reject the input.
    # -----------------------------------------

    assert data_output["passed"] is False

    assert len(
        data_output["missing_lot_measurements"]
    ) == 1

    missing = data_output[
        "missing_lot_measurements"
    ][0]

    assert (
        missing["field"]
        == "leakage_0h_population"
    )

    assert missing["index"] == 2

    # -----------------------------------------
    # Hard-stop verification
    #
    # No analytical agent is allowed to consume
    # invalid lot evidence.
    # -----------------------------------------

    assert (
        "lot_intelligence"
        not in result.agent_outputs
    )

    assert (
        "drift_intelligence"
        not in result.agent_outputs
    )

    assert (
        "latent_defect"
        not in result.agent_outputs
    )

    assert (
        "adversarial_qa"
        not in result.agent_outputs
    )

    assert (
        "reliability_judge"
        not in result.agent_outputs
    )

    assert (
        "explanation"
        not in result.agent_outputs
    )

    # -----------------------------------------
    # No decision may be fabricated because the
    # Reliability Judge never executed.
    # -----------------------------------------

    assert result.final_decision is None

    assert (
        result.status
        == WorkflowStatus.NEEDS_REVIEW
    )

@pytest.mark.asyncio
async def test_orchestrator_v2_nan_lot_value_guardrail():
    state = WorkflowState(
        workflow_id="wf-nan-lot-value-v2",
        component_id="NAN-LOT-VALUE-V2",
        lot_id="LOT-001",
        raw_data={
            "leakage_0h": 10.0,
            "leakage_24h": 10.2,
        },
        lot_context=LotContext(
            lot_id="LOT-001",
            component_ids=[
                "PEER-001",
                "PEER-002",
                "PEER-003",
            ],
            leakage_0h_population=[
                9.8,
                float("nan"),
                10.1,
            ],
            leakage_24h_population=[
                9.9,
                10.0,
                10.2,
            ],
        ),
    )

    result = await SentinelOrchestrator().run(
        state
    )

    data_output = result.agent_outputs[
        "data_forensics"
    ]

    assert data_output["passed"] is False

    assert len(
        data_output["invalid_lot_measurements"]
    ) == 1

    assert (
        "lot_intelligence"
        not in result.agent_outputs
    )

    assert (
        "reliability_judge"
        not in result.agent_outputs
    )

    assert result.final_decision is None

    assert (
        result.status
        == WorkflowStatus.NEEDS_REVIEW
    )