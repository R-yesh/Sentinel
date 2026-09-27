from agents.base import BaseAgent
from llm.client import generate_structured
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState, WorkflowStatus
from shared.schemas.judge import JudgeDecision


class ReliabilityJudgeAgent(BaseAgent):
    name = "reliability_judge"

    async def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:
        latent_output = state.agent_outputs.get(
            "latent_defect",
            {},
        )

        adversarial_output = state.agent_outputs.get(
            "adversarial_qa",
            {},
        )

        assessment = latent_output.get(
            "assessment"
        )

        review = adversarial_output.get(
            "review"
        )

        # -----------------------------------------
        # Guardrail
        # -----------------------------------------

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
                summary=(
                    "Reliability Judge requires human review "
                    "because sufficient evidence is unavailable."
                ),
                evidence=[
                    (
                        "Required latent or adversarial "
                        "evidence is unavailable."
                    )
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
                "supporting_evidence": [],
                "unresolved_concerns": [
                    (
                        "Required latent or adversarial "
                        "evidence is unavailable."
                    )
                ],
            }

            state.status = WorkflowStatus.NEEDS_REVIEW

            return state

        signals = latent_output.get(
            "signals",
            [],
        )

        # -----------------------------------------
        # Lot Intelligence V2 evidence
        # -----------------------------------------

        robust_z_score = latent_output.get(
            "robust_z_score"
        )

        robust_anomaly_score = latent_output.get(
            "robust_anomaly_score"
        )

        deviation_direction = latent_output.get(
            "deviation_direction"
        )

        lot_evidence_level = latent_output.get(
            "lot_evidence_level"
        )

        isolation_score = latent_output.get(
            "isolation_score"
        )

        isolation_anomaly = latent_output.get(
            "isolation_anomaly"
        )

        # -----------------------------------------
        # Drift / forecast evidence
        # -----------------------------------------

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

        Activated Sentinel signals:
        {signals}

        Lot-relative statistical evidence:
        - Robust z-score: {robust_z_score}
        - Robust anomaly score: {robust_anomaly_score}
        - Deviation direction: {deviation_direction}
        - Lot evidence level: {lot_evidence_level}

        Multivariate lot evidence:
        - Isolation Forest anomaly score:
          {isolation_score}
        - Isolation Forest anomaly classification:
          {isolation_anomaly}

        Observed early drift evidence:
        - Early leakage percentage change:
          {percentage_change}%
        - Early leakage slope:
          {early_slope} uA/h

        Model-derived forecast evidence:
        - Predicted 168h leakage:
          {predicted_168h} uA
        - Prediction uncertainty:
          {prediction_uncertainty} uA

        Adversarial review:
        {review}

        Decision principles:

        1. Do not simply count activated signals or
        adversarial arguments. Evaluate their meaning
        and substance.

        2. Distinguish observed and derived-from-observation
        evidence from model-derived evidence.

        Early leakage percentage change and early slope are
        deterministic quantities derived from observed 0h
        and 24h measurements.

        Predicted 168h leakage and prediction uncertainty
        are model-derived evidence.

        3. Robust lot statistics describe how unusual the
        component's 24h leakage is relative to its
        manufacturing lot.

        A positive robust z-score indicates high-side
        deviation. A negative robust z-score indicates
        low-side deviation.

        A low-side deviation may be statistically unusual,
        but it is not evidence of the elevated-leakage
        defect mode Sentinel is assessing.

        4. The robust z-score is a standardized robust
        deviation statistic.

        The robust anomaly score is a derived normalized
        magnitude used by Sentinel.

        Neither value is a calibrated probability,
        defect probability, or risk score.

        5. Isolation Forest evaluates whether the
        component's multivariate early leakage behaviour
        is unusual relative to its lot peers.

        An Isolation Forest anomaly is evidence of unusual
        behaviour. It does not by itself prove a defect,
        identify a physical failure mechanism, or represent
        a probability of failure.

        6. Robust statistics and Isolation Forest provide
        complementary analytical views.

        Agreement between high-side robust deviation,
        Isolation Forest anomaly, and observed early drift
        may provide meaningful corroborating evidence.

        However, do not treat detector agreement as
        independent probabilities and do not convert
        agreement into an invented combined probability
        or risk score.

        7. Detector disagreement is not automatically
        evidence for PASS, REVIEW, or REJECT.

        Interpret why the detectors disagree.

        For example, a component may have statistically
        typical absolute 24h leakage while exhibiting an
        unusual multivariate early trajectory.

        Choose REVIEW only if such disagreement creates a
        material unresolved ambiguity that could
        realistically change the reliability disposition.

        8. The predicted 168h leakage is a model forecast,
        not an observed measurement.

        Early leakage behaviour may change over the
        remainder of burn-in. Do not assume linear
        continuation without qualification.

        9. Prediction uncertainty represents disagreement
        among Random Forest tree predictions.

        It is not a calibrated confidence interval,
        direct probability of prediction error, or
        probability of component failure.

        10. Adversarial arguments are competing
        interpretations of existing evidence.
        They are not additional measurements.

        A standalone Isolation Forest anomaly is an
        analytical observation, not automatically a
        material reliability conflict.

        Give it substantially greater weight when it is
        corroborated by observed early drift or high-side
        lot-relative deviation.

        An isolated Isolation Forest flag with reassuring
        observed drift and typical robust lot evidence
        is not, by itself, sufficient reason for REVIEW.

        11. Weight direct observed degradation and
        corroborating lot-relative evidence more heavily
        than generic model limitations.

        Ask whether an adversarial concern materially
        changes the interpretation of the evidence.

        12. Do not independently redefine or recalibrate
        Sentinel's deterministic signal thresholds.

        If an upstream signal is activated, treat its
        activation as established according to Sentinel's
        calibrated analysis.

        Do not dismiss an activated signal as insignificant
        merely because its numerical magnitude appears
        small in isolation.

        You may weigh that signal against genuinely
        conflicting evidence.

        Decision meanings:

        PASS:

        Choose PASS when the observed evidence is
        reassuring and there is no substantial evidence
        of abnormal reliability behaviour.

        Normal model uncertainty, forecast limitations,
        or ordinary detector imperfections are NOT by
        themselves sufficient reasons to choose REVIEW.

        REVIEW:

        Choose REVIEW only when there is a MATERIAL
        unresolved conflict or insufficiency that could
        realistically change the reliability disposition.

        A limitation is material only if resolving it
        could plausibly change the component from
        acceptable to unacceptable, or vice versa.

        Do not choose REVIEW merely because uncertainty
        exists.

        REJECT:

        Choose REJECT when strong evidence provides
        substantial reliability concern, especially when
        observed early degradation is corroborated by
        multiple meaningful analytical views.

        REJECT does not require certainty about the exact
        future 168h leakage value when observed early
        behaviour and corroborating evidence already
        establish substantial concern.

        Generic forecast uncertainty does not negate
        strong observed evidence.

        Final requirements:

        - Choose exactly PASS, REVIEW, or REJECT.
        - Base the decision only on supplied evidence.
        - Do not invent thresholds, measurements,
          probabilities, physical causes, or failure
          mechanisms.
        - Do not reinterpret anomaly scores as failure
          probabilities.
        - Clearly identify the evidence that actually
          drove the decision.
        - Clearly identify any material unresolved
          concerns.
        """

        judge_result = generate_structured(
            prompt=prompt,
            response_schema=JudgeDecision,
        )

        decision = judge_result.decision.value
        reason_code = (
            judge_result.reason_code.value
        )

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
            summary=(
                f"Reliability Judge recommends "
                f"{decision}."
            ),
            evidence=(
                judge_result.supporting_evidence
            ),
            metadata={
                "decision": decision,
                "reason_code": reason_code,
                "reasoning": (
                    judge_result.reasoning
                ),
                "unresolved_concerns": (
                    judge_result.unresolved_concerns
                ),
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "decision": decision,
            "reason_code": reason_code,
            "reasoning": (
                judge_result.reasoning
            ),
            "supporting_evidence": (
                judge_result.supporting_evidence
            ),
            "unresolved_concerns": (
                judge_result.unresolved_concerns
            ),
        }

        state.final_decision = decision

        if decision == "REVIEW":
            state.status = (
                WorkflowStatus.NEEDS_REVIEW
            )
        else:
            state.status = (
                WorkflowStatus.COMPLETED
            )

        return state