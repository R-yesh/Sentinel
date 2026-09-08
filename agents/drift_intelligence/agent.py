from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class DriftIntelligenceAgent(BaseAgent):
    name = "drift_intelligence"

    async def run(self, state: WorkflowState) -> WorkflowState:
        value_0h = state.raw_data.get("leakage_0h")
        value_24h = state.raw_data.get("leakage_24h")

        if value_0h is None or value_24h is None:
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

        change = value_24h - value_0h
        drift_rate = change / 24

        projected_168h = value_0h + (drift_rate * 168)

        if value_0h != 0:
            percentage_change = (change / value_0h) * 100
        else:
            percentage_change = 0.0

        if percentage_change >= 20:
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
                f"Leakage at 0h: {value_0h:.2f} uA.",
                f"Leakage at 24h: {value_24h:.2f} uA.",
                f"Early leakage change: {percentage_change:.2f}%.",
                f"Linear 168h projection: {projected_168h:.2f} uA.",
            ],
            metadata={
                "value_0h": value_0h,
                "value_24h": value_24h,
                "change": change,
                "percentage_change": percentage_change,
                "drift_rate_per_hour": drift_rate,
                "projected_168h": projected_168h,
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "percentage_change": percentage_change,
            "drift_rate_per_hour": drift_rate,
            "projected_168h": projected_168h,
            "passed": percentage_change < 20,
        }

        return state