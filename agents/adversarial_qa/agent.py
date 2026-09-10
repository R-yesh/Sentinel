from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class AdversarialQAAgent(BaseAgent):
    name = "adversarial_qa"

    async def run(self, state: WorkflowState) -> WorkflowState:
        latent_output = state.agent_outputs.get("latent_defect", {})
        lot_output = state.agent_outputs.get("lot_intelligence", {})
        drift_output = state.agent_outputs.get("drift_intelligence", {})

        latent_risk = latent_output.get("risk_score")

        if latent_risk is None:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="unable_to_challenge",
                severity=Severity.MEDIUM,
                score=0.5,
                confidence=0.6,
                summary="Adversarial review could not be completed.",
                evidence=[
                    "Latent defect risk score is unavailable."
                ],
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "challenge_strength": None,
                "reason": "insufficient_evidence",
            }

            return state

        challenges = []

        lot_anomaly_score = lot_output.get("anomaly_score")
        projected_168h = drift_output.get("projected_168h")

        if lot_anomaly_score is not None and lot_anomaly_score < 0.5:
            challenges.append(
                "Lot-level statistical evidence does not strongly support an outlier classification."
            )

        if projected_168h is not None:
            challenges.append(
                "The 168h value is currently based on extrapolation rather than an observed measurement."
            )

        challenges.append(
            "Early drift may not remain linear throughout the full burn-in period."
        )

        if latent_risk >= 0.7:
            challenge_strength = 0.3
        elif latent_risk >= 0.4:
            challenge_strength = 0.6
        else:
            challenge_strength = 0.8

        if challenge_strength >= 0.7:
            severity = Severity.HIGH
            finding_type = "strong_adversarial_challenge"

        elif challenge_strength >= 0.4:
            severity = Severity.MEDIUM
            finding_type = "moderate_adversarial_challenge"

        else:
            severity = Severity.INFO
            finding_type = "weak_adversarial_challenge"

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            score=challenge_strength,
            confidence=0.75,
            summary=(
                "Adversarial QA reviewed the latent defect conclusion "
                "and searched for plausible counterarguments."
            ),
            evidence=challenges,
            metadata={
                "latent_risk": latent_risk,
                "challenge_strength": challenge_strength,
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "challenge_strength": challenge_strength,
            "challenges": challenges,
        }

        return state