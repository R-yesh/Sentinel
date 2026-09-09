from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class ExplanationAgent(BaseAgent):
    name = "explanation"

    async def run(self, state: WorkflowState) -> WorkflowState:
        judge_output = state.agent_outputs.get("reliability_judge", {})
        lot_output = state.agent_outputs.get("lot_intelligence", {})
        drift_output = state.agent_outputs.get("drift_intelligence", {})
        latent_output = state.agent_outputs.get("latent_defect", {})
        adversarial_output = state.agent_outputs.get("adversarial_qa", {})

        decision = judge_output.get("decision", "UNKNOWN")
        reason_code = judge_output.get("reason_code", "UNKNOWN")

        lot_ratio = lot_output.get("deviation_ratio")
        drift_change = drift_output.get("percentage_change")
        projected_168h = drift_output.get("projected_168h")
        latent_risk = latent_output.get("risk_score")
        challenge_strength = adversarial_output.get("challenge_strength")

        explanation_parts = [
            f"Sentinel recommends {decision} for component {state.component_id}."
        ]

        if lot_ratio is not None:
            explanation_parts.append(
                f"The component measures {lot_ratio:.2f}x the lot baseline."
            )

        if drift_change is not None:
            explanation_parts.append(
                f"Early leakage changed by {drift_change:.2f}%."
            )

        if projected_168h is not None:
            explanation_parts.append(
                f"The current 168h projection is {projected_168h:.2f} uA."
            )

        if latent_risk is not None:
            explanation_parts.append(
                f"The combined latent-defect risk score is {latent_risk:.2f}."
            )

        if challenge_strength is not None:
            explanation_parts.append(
                f"Adversarial review produced a challenge strength "
                f"of {challenge_strength:.2f}."
            )

        explanation_parts.append(
            f"The Reliability Judge reached this decision under "
            f"reason code {reason_code}."
        )

        explanation = " ".join(explanation_parts)

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type="qa_explanation",
            severity=Severity.INFO,
            score=0.0,
            confidence=1.0,
            summary="Generated inspector-facing explanation.",
            evidence=[explanation],
            metadata={
                "decision": decision,
                "reason_code": reason_code,
            },
        )

        state.findings.append(finding)
        state.explanation = explanation

        state.agent_outputs[self.name] = {
            "explanation": explanation,
        }

        return state