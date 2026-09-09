from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState, WorkflowStatus


class ReliabilityJudgeAgent(BaseAgent):
    name = "reliability_judge"

    async def run(self, state: WorkflowState) -> WorkflowState:
        latent_output = state.agent_outputs.get("latent_defect", {})
        adversarial_output = state.agent_outputs.get("adversarial_qa", {})

        latent_risk = latent_output.get("risk_score")
        challenge_strength = adversarial_output.get("challenge_strength")

        if latent_risk is None or challenge_strength is None:
            decision = "REVIEW"
            reason_code = "INSUFFICIENT_EVIDENCE"
            severity = Severity.MEDIUM
            confidence = 0.5

        elif latent_risk >= 0.7 and challenge_strength < 0.5:
            decision = "REJECT"
            reason_code = "HIGH_RISK_WEAK_CHALLENGE"
            severity = Severity.CRITICAL
            confidence = 0.9

        elif latent_risk < 0.4 and challenge_strength >= 0.7:
            decision = "PASS"
            reason_code = "LOW_RISK_STRONG_CHALLENGE"
            severity = Severity.INFO
            confidence = 0.85

        else:
            decision = "REVIEW"
            reason_code = "CONFLICTING_EVIDENCE"
            severity = Severity.HIGH
            confidence = 0.7

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type="reliability_decision",
            severity=severity,
            score=latent_risk if latent_risk is not None else 0.5,
            confidence=confidence,
            summary=f"Reliability Judge recommends {decision}.",
            evidence=[
                f"Latent defect risk: {latent_risk}.",
                f"Adversarial challenge strength: {challenge_strength}.",
                f"Decision reason: {reason_code}.",
            ],
            metadata={
                "decision": decision,
                "reason_code": reason_code,
            },
        )

        state.findings.append(finding)

        state.final_decision = decision

        state.agent_outputs[self.name] = {
            "decision": decision,
            "reason_code": reason_code,
            "confidence": confidence,
        }

        if decision == "REVIEW":
            state.status = WorkflowStatus.NEEDS_REVIEW
        else:
            state.status = WorkflowStatus.COMPLETED

        return state