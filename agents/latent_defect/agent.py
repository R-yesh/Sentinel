from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class LatentDefectAgent(BaseAgent):
    name = "latent_defect"

    async def run(self, state: WorkflowState) -> WorkflowState:
        lot_output = state.agent_outputs.get("lot_intelligence", {})
        drift_output = state.agent_outputs.get("drift_intelligence", {})

        lot_anomaly_score = lot_output.get("anomaly_score")
        drift_change = drift_output.get("percentage_change")
        predicted_168h = drift_output.get("predicted_168h")

        if lot_anomaly_score is None or drift_change is None:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="insufficient_combined_evidence",
                severity=Severity.MEDIUM,
                score=0.5,
                confidence=0.6,
                summary="Insufficient evidence to estimate latent defect risk.",
                evidence=[
                    "Lot and drift intelligence outputs are both required."
                ],
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "risk_score": None,
                "passed": False,
                "reason": "insufficient_evidence",
            }

            return state

        lot_risk = lot_anomaly_score
        drift_risk = min(abs(drift_change) / 50.0, 1.0)

        risk_score = (
            0.45 * lot_risk
            + 0.55 * drift_risk
        )

        if risk_score >= 0.7:
            severity = Severity.CRITICAL
            finding_type = "high_latent_defect_risk"

        elif risk_score >= 0.4:
            severity = Severity.HIGH
            finding_type = "moderate_latent_defect_risk"

        else:
            severity = Severity.INFO
            finding_type = "low_latent_defect_risk"

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            score=risk_score,
            confidence=0.8,
            summary=(
                "Latent defect risk was estimated by combining "
                "lot deviation and early drift behaviour."
            ),
            evidence=[
                f"Lot anomaly score: {lot_anomaly_score:.2f}.",
                f"Early drift change: {drift_change:.2f}%.",
                (
                    f"predicted 168h leakage: {predicted_168h:.2f} uA."
                    if predicted_168h is not None
                    else "predicted 168h leakage unavailable."
                ),
            ],
            metadata={
                "lot_risk": lot_risk,
                "drift_risk": drift_risk,
                "risk_score": risk_score,
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "risk_score": risk_score,
            "passed": risk_score < 0.4,
        }

        return state