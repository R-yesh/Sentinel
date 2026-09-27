from agents.base import BaseAgent
from llm.client import generate_structured
from shared.schemas.adversarial import AdversarialReview
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class AdversarialQAAgent(BaseAgent):
    name = "adversarial_qa"

    async def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:
        latent_output = state.agent_outputs.get(
            "latent_defect",
            {},
        )

        assessment = latent_output.get(
            "assessment"
        )

        if (
            assessment is None
            or assessment == "INSUFFICIENT_EVIDENCE"
        ):
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="unable_to_challenge",
                severity=Severity.MEDIUM,
                summary=(
                    "Adversarial review could not be completed."
                ),
                evidence=[
                    (
                        "Latent defect assessment is unavailable "
                        "or contains insufficient evidence."
                    )
                ],
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "review": None,
                "reason": "insufficient_evidence",
            }

            return state

        signals = latent_output.get(
            "signals",
            [],
        )

        # Lot-relative statistical evidence
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

        # Isolation Forest evidence
        isolation_score = latent_output.get(
            "isolation_score"
        )

        isolation_anomaly = latent_output.get(
            "isolation_anomaly"
        )

        # Drift / prediction evidence
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
        You are the Adversarial QA Agent in Sentinel,
        a semiconductor burn-in reliability analysis system.

        Your job is to critically challenge a provisional
        latent-defect assessment.

        You are NOT the final decision maker.

        Component:
        {state.component_id}

        Provisional latent-defect assessment:
        {assessment}

        Activated signals:
        {signals}

        Lot-relative statistical evidence:
        - Robust z-score: {robust_z_score}
        - Robust anomaly score: {robust_anomaly_score}
        - Deviation direction: {deviation_direction}
        - Lot evidence level: {lot_evidence_level}

        Multivariate lot evidence:
        - Isolation Forest anomaly score: {isolation_score}
        - Isolation Forest anomaly classification:
          {isolation_anomaly}

        Drift and forecast evidence:
        - Early leakage percentage change:
          {percentage_change}%
        - Early leakage slope:
          {early_slope} uA/h
        - Predicted 168h leakage:
          {predicted_168h} uA
        - Prediction uncertainty:
          {prediction_uncertainty} uA

        Interpretation constraints:

        1. Robust lot statistics and Isolation Forest
        provide different forms of lot-relative evidence.

        Robust statistics describe how the component's
        24h leakage differs from the lot distribution.

        Isolation Forest evaluates whether the component's
        multivariate early leakage behaviour is unusual
        relative to its lot peers.

        Do not treat agreement between them as independent
        probabilities.

        2. A TYPICAL robust evidence level does not prove
        that an individual component is safe.

        Likewise, the absence of an Isolation Forest
        anomaly does not prove that the component is safe.

        These results only describe the evidence detected
        by their respective methods.

        3. LOW-side robust deviations are statistically
        unusual but are not evidence of the elevated-leakage
        defect mode Sentinel is assessing.

        4. An Isolation Forest anomaly indicates unusual
        multivariate early behaviour. It does NOT by itself
        identify a physical defect, failure mechanism, or
        probability of failure.

        5. The Isolation Forest anomaly score is a model
        anomaly measure. Do not interpret it as a calibrated
        probability, defect probability, or risk score.

        6. A standalone Isolation Forest anomaly is an
        analytical observation, not automatically a
        reliability concern or material conflict.

        Treat an Isolation Forest anomaly as stronger
        evidence when it is corroborated by observed
        early drift or high-side lot-relative deviation.

        If observed drift is reassuring and robust
        lot-relative evidence is typical, an isolated
        Isolation Forest flag should not by itself
        create a REVIEW argument.

        7. Prediction uncertainty represents disagreement
        among Random Forest tree predictions. It is NOT
        a calibrated confidence interval or direct
        probability of prediction error.

        8. The predicted 168h leakage is a model forecast,
        not an observed measurement.

        9. Early leakage behaviour may change over the
        remainder of burn-in. Do not assume linear
        continuation without qualification.

        10. Activated signals are evidence indicators,
        not independent probabilities.

        11. Agreement between high-side robust deviation,
        Isolation Forest anomaly, and observed early drift
        may provide corroborating evidence because different
        analytical views point toward unusual behaviour.

        However, do not describe this agreement as proof
        of a latent defect.

        12. Disagreement between detectors may itself be
        relevant to the review.

        For example, Isolation Forest may identify unusual
        multivariate behaviour while the component remains
        statistically typical in its absolute 24h leakage.

        Treat such disagreement as evidence requiring
        interpretation, not automatically as evidence
        for either higher or lower concern.

        Your task:

        - Search for evidence that could LOWER concern.
        - Search for evidence that could INCREASE concern.
        - Identify genuine conflicts between evidence sources.
        - Identify uncertainty or assumptions that materially
          affect the reliability assessment and may warrant
          REVIEW.
        - Do not manufacture a REVIEW argument merely because
          models and forecasts inherently contain uncertainty.
        - Challenge both overly pessimistic and overly
          reassuring interpretations.
        - Do not issue PASS, REVIEW, or REJECT.
        - Do not invent measurements, thresholds, physical
          causes, or failure mechanisms.
        - Base every challenge only on the evidence supplied
          above.
        """

        review = generate_structured(
            prompt=prompt,
            response_schema=AdversarialReview,
        )

        challenge_evidence = [
            (
                f"[{challenge.direction.value}] "
                f"{challenge.challenge_type.value}: "
                f"{challenge.summary}"
            )
            for challenge in review.challenges
        ]

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type="adversarial_review",
            severity=Severity.INFO,
            summary=(
                "Adversarial QA stress-tested the provisional "
                "latent-defect assessment."
            ),
            evidence=challenge_evidence,
            metadata={
                "challenged_assessment": (
                    review.challenged_assessment
                ),
                "unresolved_conflict": (
                    review.unresolved_conflict
                ),
                "challenge_count": len(
                    review.challenges
                ),
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "review": review.model_dump(),
        }

        return state