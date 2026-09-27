from agents.base import BaseAgent
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState

from shared.config.signal_thresholds import (
    EARLY_DRIFT_THRESHOLD,
    UNCERTAINTY_THRESHOLD,
)


class LatentDefectAgent(BaseAgent):
    name = "latent_defect"

    async def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:
        lot_output = state.agent_outputs.get(
            "lot_intelligence",
            {},
        )

        drift_output = state.agent_outputs.get(
            "drift_intelligence",
            {},
        )

        # Lot Intelligence evidence
        robust_z_score = lot_output.get(
            "robust_z_score"
        )

        robust_anomaly_score = lot_output.get(
            "robust_anomaly_score"
        )

        deviation_direction = lot_output.get(
            "deviation_direction"
        )

        evidence_level = lot_output.get(
            "evidence_level"
        )

        isolation_score = lot_output.get(
            "isolation_score"
        )

        isolation_anomaly = lot_output.get(
            "isolation_anomaly"
        )

        # Drift Intelligence evidence
        drift_change = drift_output.get(
            "percentage_change"
        )

        early_slope = drift_output.get(
            "early_slope"
        )

        predicted_168h = drift_output.get(
            "predicted_168h"
        )

        prediction_uncertainty = drift_output.get(
            "prediction_uncertainty"
        )

        # Both upstream evidence sources are required.
        if (
            evidence_level is None
            or isolation_anomaly is None
            or drift_change is None
        ):
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="insufficient_combined_evidence",
                severity=Severity.MEDIUM,
                summary=(
                    "Insufficient evidence to estimate "
                    "latent defect concern."
                ),
                evidence=[
                    (
                        "Lot Intelligence and Drift Intelligence "
                        "outputs are both required."
                    )
                ],
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "assessment": "INSUFFICIENT_EVIDENCE",
                "signal_count": 0,
                "signals": [],
                "reason": "insufficient_evidence",
            }

            return state

        # -------------------------------------------------
        # Determine analytical conditions first
        # -------------------------------------------------

        has_elevated_lot_deviation = (
            deviation_direction == "HIGH"
            and evidence_level == "ELEVATED"
        )

        has_strong_lot_deviation = (
            deviation_direction == "HIGH"
            and evidence_level == "STRONG_DEVIATION"
        )

        has_lot_outlier = (
            deviation_direction == "HIGH"
            and evidence_level == "OUTLIER"
        )

        has_lot_deviation = (
            has_elevated_lot_deviation
            or has_strong_lot_deviation
            or has_lot_outlier
        )

        has_isolation_anomaly = bool(
            isolation_anomaly
        )

        has_early_drift = (
            drift_change >= EARLY_DRIFT_THRESHOLD
        )

        has_high_uncertainty = (
            prediction_uncertainty is not None
            and prediction_uncertainty
            >= UNCERTAINTY_THRESHOLD
        )

        # -------------------------------------------------
        # Promote analytical observations into
        # reliability-relevant signals
        # -------------------------------------------------

        evidence_flags = []

        if has_elevated_lot_deviation:
            evidence_flags.append(
                "elevated_lot_deviation"
            )

        if has_strong_lot_deviation:
            evidence_flags.append(
                "strong_lot_deviation"
            )

        if has_lot_outlier:
            evidence_flags.append(
                "high_side_lot_outlier"
            )

        if has_early_drift:
            evidence_flags.append(
                "significant_early_drift"
            )

        # Isolation Forest remains visible as an analytical
        # observation, but becomes a reliability signal only
        # when corroborated by observed drift or high-side
        # lot-relative deviation.
        if (
            has_isolation_anomaly
            and (
                has_early_drift
                or has_lot_deviation
            )
        ):
            evidence_flags.append(
                "multivariate_anomaly_corroboration"
            )

        # Prediction uncertainty is model-derived context.
        # It should strengthen an existing concern rather
        # than create reliability concern by itself.
        if (
            has_high_uncertainty
            and has_early_drift
        ):
            evidence_flags.append(
                "forecast_uncertainty_corroboration"
            )

        signal_count = len(evidence_flags)

        has_multivariate_corroboration = (
            "multivariate_anomaly_corroboration"
            in evidence_flags
        )

        has_uncertainty_corroboration = (
            "forecast_uncertainty_corroboration"
            in evidence_flags
        )

        # -------------------------------------------------
        # Provisional assessment
        # -------------------------------------------------

        if (
            has_early_drift
            and has_lot_deviation
            and has_multivariate_corroboration
        ):
            assessment = "HIGH_CONCERN"
            severity = Severity.CRITICAL
            finding_type = (
                "corroborated_latent_defect_concern"
            )

        elif (
            has_early_drift
            and (
                has_lot_deviation
                or has_multivariate_corroboration
            )
        ):
            assessment = "ELEVATED_CONCERN"
            severity = Severity.HIGH
            finding_type = (
                "multi_signal_latent_defect_concern"
            )

        elif has_early_drift:
            assessment = "ELEVATED_CONCERN"
            severity = Severity.HIGH
            finding_type = "early_drift_concern"

        elif (
            has_lot_deviation
            and has_multivariate_corroboration
        ):
            assessment = "ELEVATED_CONCERN"
            severity = Severity.HIGH
            finding_type = (
                "corroborated_lot_anomaly_concern"
            )

        elif has_lot_deviation:
            assessment = "ELEVATED_CONCERN"
            severity = Severity.MEDIUM
            finding_type = "lot_deviation_concern"

        else:
            assessment = "LOW_CONCERN"
            severity = Severity.INFO

            if has_isolation_anomaly:
                finding_type = (
                    "multivariate_anomaly_noted"
                )

            elif has_high_uncertainty:
                finding_type = (
                    "forecast_uncertainty_noted"
                )

            else:
                finding_type = (
                    "no_latent_defect_signals"
                )

        # -------------------------------------------------
        # Finding
        # -------------------------------------------------

        evidence = [
            (
                f"Lot evidence level: "
                f"{evidence_level}."
            ),
            (
                f"Robust z-score: "
                f"{robust_z_score:.2f}."
                if robust_z_score is not None
                else "Robust z-score unavailable."
            ),
            (
                f"Isolation Forest score: "
                f"{isolation_score:.4f}."
                if isolation_score is not None
                else "Isolation Forest score unavailable."
            ),
            (
                f"Early drift change: "
                f"{drift_change:.2f}%."
            ),
            (
                f"Predicted 168h leakage: "
                f"{predicted_168h:.2f} uA."
                if predicted_168h is not None
                else "Predicted 168h leakage unavailable."
            ),
        ]

        metadata = {
            "assessment": assessment,
            "signal_count": signal_count,
            "signals": evidence_flags,

            "robust_z_score": robust_z_score,
            "robust_anomaly_score": (
                robust_anomaly_score
            ),
            "deviation_direction": (
                deviation_direction
            ),
            "lot_evidence_level": evidence_level,

            "isolation_score": isolation_score,
            "isolation_anomaly": isolation_anomaly,

            "percentage_change": drift_change,
            "early_slope": early_slope,
            "predicted_168h": predicted_168h,
            "prediction_uncertainty": (
                prediction_uncertainty
            ),
        }

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            summary=(
                "Latent defect evidence was synthesized "
                f"into a provisional {assessment} assessment."
            ),
            evidence=evidence,
            metadata=metadata,
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = metadata

        return state