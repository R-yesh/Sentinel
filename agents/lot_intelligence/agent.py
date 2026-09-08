from statistics import mean

from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class LotIntelligenceAgent(BaseAgent):
    name = "lot_intelligence"

    async def run(self, state: WorkflowState) -> WorkflowState:
        component_value = state.raw_data.get("leakage_24h")
        lot_values = state.raw_data.get("lot_leakage_24h", [])

        if component_value is None or not lot_values:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="insufficient_lot_data",
                severity=Severity.MEDIUM,
                score=0.5,
                confidence=1.0,
                summary="Insufficient data for lot-level comparison.",
                evidence=[
                    "Component measurement or peer lot measurements are missing."
                ],
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "passed": False,
                "reason": "insufficient_data",
            }

            return state

        lot_mean = mean(lot_values)

        deviation_ratio = component_value / lot_mean

        if deviation_ratio >= 2.0:
            severity = Severity.HIGH
            score = min(deviation_ratio / 5.0, 1.0)
            finding_type = "lot_outlier"

            summary = (
                "Component leakage is abnormally high relative "
                "to its manufacturing lot."
            )

        else:
            severity = Severity.INFO
            score = 0.0
            finding_type = "lot_baseline_pass"

            summary = (
                "Component leakage is consistent with its "
                "manufacturing lot."
            )

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            score=score,
            confidence=0.9,
            summary=summary,
            evidence=[
                f"Component leakage at 24h: {component_value:.2f} uA.",
                f"Lot mean leakage at 24h: {lot_mean:.2f} uA.",
                f"Component is {deviation_ratio:.2f}x the lot mean.",
            ],
            metadata={
                "component_value": component_value,
                "lot_mean": lot_mean,
                "deviation_ratio": deviation_ratio,
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "lot_mean": lot_mean,
            "deviation_ratio": deviation_ratio,
            "passed": deviation_ratio < 2.0,
        }

        return state