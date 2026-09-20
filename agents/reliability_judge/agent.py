from agents.base import BaseAgent
from llm.client import generate_structured
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState, WorkflowStatus
from shared.schemas.judge import JudgeDecision


class ReliabilityJudgeAgent(BaseAgent):
    name = "reliability_judge"

    async def run(self, state: WorkflowState) -> WorkflowState:
        latent_output = state.agent_outputs.get("latent_defect", {})
        adversarial_output = state.agent_outputs.get("adversarial_qa", {})

        assessment = latent_output.get("assessment")

        review = adversarial_output.get("review")

        if (
            assessment is None
            or assessment == "INSUFFICIENT_EVIDENCE"
            or review is None
        ):
            decision = "REVIEW"

            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="reliability_decision",
                severity=Severity.MEDIUM,
                score=0.0,
                confidence=1.0,
                summary=(
                    "Reliability Judge requires human review "
                    "because sufficient evidence is unavailable."
                ),
                evidence=[
                    "Required latent or adversarial evidence is unavailable."
                ],
                metadata={
                    "decision": decision,
                    "reason_code": "INSUFFICIENT_EVIDENCE",
                },
            )

            state.findings.append(finding)

            state.final_decision = decision

            state.agent_outputs[self.name] = {
                "decision": decision,
                "reason_code": "INSUFFICIENT_EVIDENCE",
                "reasoning": (
                    "Required evidence was unavailable."
                ),
            }

            state.status = WorkflowStatus.NEEDS_REVIEW

            return state

        signals = latent_output.get(
            "signals",
            [],
        )

        lot_anomaly_score = latent_output.get(
            "lot_anomaly_score"
        )

        percentage_change = latent_output.get(
            "percentage_change"
        )

        early_slope = latent_output.get(
            "early_slope"
        )

        predicted_168h = latent_output.get(
            "predicted_168h"
        )

        prediction_uncertainty = latent_output.get(
            "prediction_uncertainty"
        )

        prompt = f"""
        You are the Reliability Judge in Sentinel,
        a semiconductor burn-in reliability analysis system.

        Your responsibility is to adjudicate the available
        evidence and issue the final reliability decision.

        You must choose exactly one:
        PASS, REVIEW, or REJECT.

        Provisional latent-defect assessment:
        {assessment}

        Activated signals:
        {signals}

        Component evidence:
        - Lot anomaly score: {lot_anomaly_score}
        - Early leakage percentage change: {percentage_change}%
        - Early leakage slope: {early_slope} uA/h
        - Predicted 168h leakage: {predicted_168h} uA
        - Prediction uncertainty: {prediction_uncertainty} uA

        Adversarial review:
        {review}

        Decision principles:

        1. Do not simply count adversarial arguments.
        Evaluate their substance.

        2. Distinguish observed evidence from model-derived
        evidence.

        3. Early leakage percentage change and early slope
        are derived from observed 0h and 24h measurements.

        4. Predicted 168h leakage is a model forecast and
        is not an observed measurement.

        5. Prediction uncertainty represents disagreement
        among Random Forest trees. It is not a calibrated
        confidence interval or direct probability of error.

        6. A high lot anomaly score means this component is
        statistically unusual relative to its lot. It does
        not by itself prove a systemic lot-wide defect.

        7. Adversarial arguments are competing interpretations,
        not additional measurements.

        Decision meanings:

        Decision meanings:

        PASS:
        Choose PASS when the observed evidence is reassuring
        and there is no substantial evidence of abnormal
        reliability behaviour.

        Normal model uncertainty or the general limitation
        that a forecast is not an observed measurement is
        NOT, by itself, sufficient reason to choose REVIEW.

        REVIEW:
        Choose REVIEW only when there is a MATERIAL unresolved
        conflict that could realistically change the reliability
        decision.

        A limitation is material only if resolving it could
        plausibly change the component from acceptable to
        unacceptable, or vice versa.

        Do not choose REVIEW merely because uncertainty exists.
        All model forecasts contain uncertainty.

        REJECT:
        Choose REJECT when strong observed evidence provides
        substantial reliability concern, especially when
        multiple independent observed indicators corroborate
        one another.

        A model forecast being uncertain does NOT negate strong
        observed evidence. REJECT does not require certainty
        about the exact future 168h leakage value if the observed
        early behaviour already provides strong corroborated
        evidence of reliability concern.

        8. Weight observed evidence more heavily than generic
        model limitations.

        Ask whether an adversarial concern actually changes the
        interpretation of the observed evidence.

        For example, uncertainty in the exact 168h forecast does
        not meaningfully weaken severe observed early degradation.
        Likewise, ordinary forecast uncertainty should not turn
        otherwise healthy observed behaviour into REVIEW.

        9. Do not independently redefine or recalibrate Sentinel's
        deterministic signal thresholds.

        If a signal is activated, treat that activation as established
        evidence from the upstream calibrated analysis.

        For example, if "significant_early_drift" is activated, do not
        dismiss the underlying drift as insignificant, negligible, or
        reassuring merely because its numerical magnitude appears small
        in isolation.

        You may still weigh an activated signal against conflicting
        evidence, but do not override the meaning of the calibrated
        signal itself.
        """

        judge_result = generate_structured(
            prompt=prompt,
            response_schema=JudgeDecision,
        )

        decision = judge_result.decision.value
        reason_code = judge_result.reason_code.value

        if decision == "REJECT":
            severity = Severity.CRITICAL

        elif decision == "REVIEW":
            severity = Severity.HIGH

        else:
            severity = Severity.INFO

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type="reliability_decision",
            severity=severity,
            score=0.0,
            confidence=0.8,
            summary=(
                f"Reliability Judge recommends {decision}."
            ),
            evidence=judge_result.supporting_evidence,
            metadata={
                "decision": decision,
                "reason_code": reason_code,
                "reasoning": judge_result.reasoning,
                "unresolved_concerns": (
                    judge_result.unresolved_concerns
                ),
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "decision": decision,
            "reason_code": reason_code,
            "reasoning": judge_result.reasoning,
            "supporting_evidence": (
                judge_result.supporting_evidence
            ),
            "unresolved_concerns": (
                judge_result.unresolved_concerns
            ),
        }

        state.final_decision = decision

        if decision == "REVIEW":
            state.status = WorkflowStatus.NEEDS_REVIEW
        else:
            state.status = WorkflowStatus.COMPLETED

        return state