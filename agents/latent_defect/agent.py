from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState

from shared.config.signal_thresholds import (
    EARLY_DRIFT_THRESHOLD,
    LOT_ANOMALY_THRESHOLD,
    UNCERTAINTY_THRESHOLD,
)

class LatentDefectAgent(BaseAgent):
    name = "latent_defect"

    async def run(self, state: WorkflowState) -> WorkflowState:
        lot_output = state.agent_outputs.get("lot_intelligence", {})
        drift_output = state.agent_outputs.get("drift_intelligence", {})

        lot_anomaly_score = lot_output.get("anomaly_score")

        drift_change = drift_output.get("percentage_change")
        early_slope = drift_output.get("early_slope")
        predicted_168h = drift_output.get("predicted_168h")
        prediction_uncertainty = drift_output.get("prediction_uncertainty")

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
                "assessment": "INSUFFICIENT_EVIDENCE",
                "evidence_strength": None,
                "signal_count": 0,
                "signals": [],
                "reason": "insufficient_evidence",
            }

            return state

        evidence_flags = []

        if lot_anomaly_score >= LOT_ANOMALY_THRESHOLD:
            evidence_flags.append(
                "strong_lot_anomaly"
            )

        if drift_change >= EARLY_DRIFT_THRESHOLD:
            evidence_flags.append(
                "significant_early_drift"
            )

        if (
            prediction_uncertainty is not None
            and prediction_uncertainty >= UNCERTAINTY_THRESHOLD
        ):
            evidence_flags.append(
                "high_prediction_uncertainty"
            )

        signal_count = len(evidence_flags)

        evidence_strength = (
            signal_count / 3.0
        )

        has_lot_anomaly = (
            "strong_lot_anomaly" in evidence_flags
        )

        has_early_drift = (
            "significant_early_drift" in evidence_flags
        )

        has_high_uncertainty = (
            "high_prediction_uncertainty" in evidence_flags
        )

        if has_early_drift and has_lot_anomaly:
            assessment = "HIGH_CONCERN"
            severity = Severity.CRITICAL
            finding_type = "corroborated_latent_defect_concern"

        elif has_early_drift and has_high_uncertainty:
            assessment = "ELEVATED_CONCERN"
            severity = Severity.HIGH
            finding_type = "elevated_latent_defect_concern"

        elif has_early_drift:
            assessment = "ELEVATED_CONCERN"
            severity = Severity.HIGH
            finding_type = "early_drift_concern"

        elif has_lot_anomaly:
            assessment = "ELEVATED_CONCERN"
            severity = Severity.HIGH
            finding_type = "lot_anomaly_concern"

        elif has_high_uncertainty:
            assessment = "ELEVATED_CONCERN"
            severity = Severity.MEDIUM
            finding_type = "forecast_uncertainty_concern"

        else:
            assessment = "LOW_CONCERN"
            severity = Severity.INFO
            finding_type = "no_latent_defect_signals"



        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            score=evidence_strength,
            confidence=0.8,
            summary=(
                "Latent defect evidence was synthesized "
                f"into a provisional {assessment} assessment."
            ),
            evidence=[
                f"Lot anomaly score: {lot_anomaly_score:.2f}.",
                f"Early drift change: {drift_change:.2f}%.",
                (
                    f"predicted 168h leakage: {predicted_168h:.2f} uA."
                    if predicted_168h is not None
                    else "Predicted 168h leakage unavailable."
                ),
            ],
            metadata={
                "assessment": assessment,
                "evidence_strength": evidence_strength,
                "signal_count": signal_count,
                "signals": evidence_flags,
                "lot_anomaly_score": lot_anomaly_score,
                "percentage_change": drift_change,
                "early_slope": early_slope,
                "predicted_168h": predicted_168h,
                "prediction_uncertainty": (
                    prediction_uncertainty
                ),
            },
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "assessment": assessment,
            "evidence_strength": evidence_strength,
            "signal_count": signal_count,
            "signals": evidence_flags,
            "lot_anomaly_score": lot_anomaly_score,
            "percentage_change": drift_change,
            "early_slope": early_slope,
            "predicted_168h": predicted_168h,
            "prediction_uncertainty": (
                prediction_uncertainty
            ),
        }

        return state