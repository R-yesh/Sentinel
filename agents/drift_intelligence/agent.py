import pandas as pd

from agents.base import BaseAgent
from ml.drift.predictor import predict_168h
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState

EARLY_DRIFT_THRESHOLD = 6.0

class DriftIntelligenceAgent(BaseAgent):
    name = "drift_intelligence"

    async def run(self, state: WorkflowState) -> WorkflowState:
        leakage_0h = state.raw_data.get("leakage_0h")
        leakage_24h = state.raw_data.get("leakage_24h")

        if leakage_0h is None or leakage_24h is None:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="insufficient_drift_data",
                severity=Severity.MEDIUM,
                score=0.5,
                confidence=1.0,
                summary="Insufficient early burn-in measurements for drift analysis.",
                evidence=[
                    "Both 0h and 24h leakage measurements are required."
                ],
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "passed": False,
                "reason": "insufficient_data",
            }

            return state

        change = leakage_24h - leakage_0h
        early_slope = change / 24

        component_data = pd.DataFrame(
            [
                {
                    "leakage_0h": leakage_0h,
                    "leakage_24h": leakage_24h,
                }
            ]
        )

        predictions, uncertainties = predict_168h(
            component_data
        )

        predicted_168h = float(
            predictions[0]
        )

        uncertainty = float(
            uncertainties[0]
        )

        if leakage_0h != 0:
            percentage_change = (change / leakage_0h) * 100
        else:
            percentage_change = 0.0

        if percentage_change >= EARLY_DRIFT_THRESHOLD:
            severity = Severity.HIGH
            finding_type = "abnormal_positive_drift"
            score = min(percentage_change / 100, 1.0)

            summary = (
                "Component leakage is increasing rapidly during "
                "early burn-in."
            )

        else:
            severity = Severity.INFO
            finding_type = "drift_baseline_pass"
            score = 0.0

            summary = (
                "Component leakage shows no significant early drift."
            )

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            score=score,
            confidence=0.75,
            summary=summary,
            evidence=[
                f"Leakage at 0h: {leakage_0h:.2f} uA.",
                f"Leakage at 24h: {leakage_24h:.2f} uA.",
                f"Early leakage change: {percentage_change:.2f}%.",
                f"Predicted 168h leakage: {predicted_168h:.2f} uA.",
            ],
            metadata={
                "leakage_0h": leakage_0h,
                "leakage_24h": leakage_24h,
                "change": change,
                "percentage_change": percentage_change,
                "early_slope": early_slope,
                "predicted_168h": predicted_168h,
                "prediction_uncertainty": uncertainty,
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "percentage_change": percentage_change,
            "early_slope": early_slope,
            "predicted_168h": predicted_168h,
            "prediction_uncertainty": uncertainty,
            "passed": percentage_change < EARLY_DRIFT_THRESHOLD,
        }

        return state