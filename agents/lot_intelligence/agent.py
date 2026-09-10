from agents.base import BaseAgent
from ml.anomaly.detector import detect_lot_anomaly
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

        result = detect_lot_anomaly(
            value=component_value,
            population=lot_values,
        )

        if result.is_outlier:
            severity = Severity.HIGH
            finding_type = "lot_outlier"
            summary = (
                "Component leakage is statistically anomalous "
                "relative to its manufacturing lot."
            )
        else:
            severity = Severity.INFO
            finding_type = "lot_baseline_pass"
            summary = (
                "Component leakage is statistically consistent "
                "with its manufacturing lot."
            )

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            score=result.anomaly_score,
            confidence=0.9,
            summary=summary,
            evidence=[
                f"Component leakage at 24h: {result.value:.2f} uA.",
                f"Lot median leakage at 24h: {result.lot_median:.2f} uA.",
                f"Lot MAD: {result.lot_mad:.2f} uA.",
                f"Robust z-score: {result.robust_z_score:.2f}.",
                f"Percentile rank: {result.percentile * 100:.1f}%.",
            ],
            metadata={
                "component_value": result.value,
                "lot_median": result.lot_median,
                "lot_mad": result.lot_mad,
                "robust_z_score": result.robust_z_score,
                "percentile": result.percentile,
                "anomaly_score": result.anomaly_score,
                "is_outlier": result.is_outlier,
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "lot_median": result.lot_median,
            "lot_mad": result.lot_mad,
            "robust_z_score": result.robust_z_score,
            "percentile": result.percentile,
            "anomaly_score": result.anomaly_score,
            "is_outlier": result.is_outlier,
            "passed": not result.is_outlier,
        }

        return state