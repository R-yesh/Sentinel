from agents.base import BaseAgent
from llm.client import generate_structured
from shared.schemas.adversarial import AdversarialReview
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class AdversarialQAAgent(BaseAgent):
    name = "adversarial_qa"

    async def run(self, state: WorkflowState) -> WorkflowState:
        latent_output = state.agent_outputs.get("latent_defect", {})

        assessment = latent_output.get("assessment")

        if (
            assessment is None
            or assessment == "INSUFFICIENT_EVIDENCE"
        ):
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="unable_to_challenge",
                severity=Severity.MEDIUM,
                score=0.0,
                confidence=1.0,
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

        Evidence:
        - Lot anomaly score: {lot_anomaly_score}
        - Early leakage percentage change: {percentage_change}%
        - Early leakage slope: {early_slope} uA/h
        - Predicted 168h leakage: {predicted_168h} uA
        - Prediction uncertainty: {prediction_uncertainty} uA

        Interpretation constraints:

        1. A low lot anomaly score does NOT prove that an
        individual component is safe. It only indicates
        weak lot-level corroboration.

        2. Prediction uncertainty represents disagreement
        among Random Forest tree predictions. It is NOT
        a calibrated confidence interval or direct
        probability of prediction error.

        3. The predicted 168h leakage is a model forecast,
        not an observed measurement.

        4. Early leakage behaviour may change over the
        remainder of burn-in. Do not assume linear
        continuation without qualification.

        5. Activated signals are evidence indicators,
        not independent probabilities.

        Your task:

        - Search for evidence that could LOWER concern.
        - Search for evidence that could INCREASE concern.
        - Identify uncertainty or assumptions that materially
        affect the reliability assessment and may warrant REVIEW.
        Do not manufacture a REVIEW argument merely because
        models and forecasts inherently contain uncertainty.
        - Challenge both overly pessimistic and overly reassuring
        interpretations.
        - Do not issue PASS, REVIEW, or REJECT.
        - Do not invent measurements or evidence.
        - Base every challenge only on the evidence supplied above.
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
            score=0.0,
            confidence=0.8,
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