from agents.base import BaseAgent
from ml.anomaly.detector import (
    DeviationDirection,
    LotEvidenceLevel,
    detect_lot_anomaly,
)
from ml.anomaly.isolation_forest import (
    build_early_feature_vector,
    detect_isolation_anomaly,
)
from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState


class LotIntelligenceAgent(BaseAgent):
    name = "lot_intelligence"

    async def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:
        leakage_0h = state.raw_data.get(
            "leakage_0h"
        )

        leakage_24h = state.raw_data.get(
            "leakage_24h"
        )

        lot_context = state.lot_context

        lot_0h_values = (
            lot_context.leakage_0h_population
            if lot_context is not None
            else []
        )

        lot_24h_values = (
            lot_context.leakage_24h_population
            if lot_context is not None
            else []
        )

        # Guardrail: required component and
        # lot evidence must exist.
        if (
            leakage_0h is None
            or leakage_24h is None
            or lot_context is None
            or not lot_0h_values
            or not lot_24h_values
        ):
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="insufficient_lot_data",
                severity=Severity.MEDIUM,
                summary=(
                    "Insufficient data for lot-relative "
                    "comparison."
                ),
                evidence=[
                    (
                        "Component measurements or manufacturing "
                        "lot context are unavailable."
                    )
                ],
                metadata={
                    "lot_id": state.lot_id,
                },
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "passed": False,
                "reason": "insufficient_lot_data",
                "lot_id": state.lot_id,
            }

            return state

        # Guardrail: both peer populations must
        # describe the same set of components.
        if len(lot_0h_values) != len(
            lot_24h_values
        ):
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="invalid_lot_context",
                severity=Severity.HIGH,
                summary=(
                    "Lot context contains inconsistent "
                    "peer measurement populations."
                ),
                evidence=[
                    (
                        "The 0h and 24h peer populations "
                        "have different sizes."
                    )
                ],
                metadata={
                    "lot_id": state.lot_id,
                    "leakage_0h_count": len(
                        lot_0h_values
                    ),
                    "leakage_24h_count": len(
                        lot_24h_values
                    ),
                },
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "passed": False,
                "reason": "invalid_lot_context",
                "lot_id": state.lot_id,
            }

            return state

        # Guardrail: supplied context must belong
        # to the component's declared lot.
        if state.lot_id != lot_context.lot_id:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="lot_context_mismatch",
                severity=Severity.HIGH,
                summary=(
                    "Component lot identity does not match "
                    "the supplied lot context."
                ),
                evidence=[
                    f"Component lot ID: {state.lot_id}.",
                    f"Context lot ID: {lot_context.lot_id}.",
                ],
                metadata={
                    "component_lot_id": state.lot_id,
                    "context_lot_id": lot_context.lot_id,
                },
            )

            state.findings.append(finding)

            state.agent_outputs[self.name] = {
                "passed": False,
                "reason": "lot_context_mismatch",
            }

            return state

        # -----------------------------------------
        # Robust statistical analysis
        # -----------------------------------------

        robust_result = detect_lot_anomaly(
            value=float(leakage_24h),
            population=lot_24h_values,
        )

        # -----------------------------------------
        # Multivariate Isolation Forest analysis
        # -----------------------------------------

        component_features = (
            build_early_feature_vector(
                leakage_0h=float(leakage_0h),
                leakage_24h=float(leakage_24h),
            )
        )

        peer_features = [
            build_early_feature_vector(
                leakage_0h=float(peer_0h),
                leakage_24h=float(peer_24h),
            )
            for peer_0h, peer_24h in zip(
                lot_0h_values,
                lot_24h_values,
            )
        ]

        isolation_result = (
            detect_isolation_anomaly(
                component_features=component_features,
                peer_features=peer_features,
            )
        )

        # -----------------------------------------
        # Normalize shared workflow values
        # -----------------------------------------

        component_value = float(
            robust_result.value
        )

        lot_median = float(
            robust_result.lot_median
        )

        lot_mad = float(
            robust_result.lot_mad
        )

        robust_z_score = float(
            robust_result.robust_z_score
        )

        percentile = float(
            robust_result.percentile
        )

        robust_anomaly_score = float(
            robust_result.anomaly_score
        )

        is_outlier = bool(
            robust_result.is_outlier
        )

        deviation_direction = (
            robust_result.deviation_direction
        )

        evidence_level = (
            robust_result.evidence_level
        )

        isolation_score = float(
            isolation_result.anomaly_score
        )

        isolation_anomaly = bool(
            isolation_result.is_anomaly
        )

        # -----------------------------------------
        # Finding interpretation
        # -----------------------------------------

        high_side_evidence = (
            deviation_direction
            == DeviationDirection.HIGH
            and evidence_level
            != LotEvidenceLevel.TYPICAL
        )

        if (
            evidence_level
            == LotEvidenceLevel.OUTLIER
        ):
            severity = Severity.HIGH
            finding_type = "high_side_lot_outlier"
            summary = (
                "Component leakage is a high-side "
                "statistical outlier relative to its "
                "manufacturing lot."
            )

        elif (
            evidence_level
            == LotEvidenceLevel.STRONG_DEVIATION
        ):
            severity = Severity.HIGH
            finding_type = "strong_lot_deviation"
            summary = (
                "Component leakage shows a strong "
                "high-side deviation relative to its "
                "manufacturing lot."
            )

        elif (
            evidence_level
            == LotEvidenceLevel.ELEVATED
        ):
            severity = Severity.MEDIUM
            finding_type = "elevated_lot_deviation"
            summary = (
                "Component leakage is elevated relative "
                "to its manufacturing lot."
            )

        elif isolation_anomaly:
            severity = Severity.MEDIUM
            finding_type = (
                "unusual_early_lot_behavior"
            )
            summary = (
                "Component early leakage behaviour is "
                "unusual relative to its manufacturing "
                "lot."
            )

        elif evidence_level in {
            LotEvidenceLevel.LOW_SIDE_DEVIATION,
            LotEvidenceLevel.LOW_SIDE_OUTLIER,
        }:
            severity = Severity.INFO
            finding_type = "low_side_lot_deviation"
            summary = (
                "Component leakage is statistically "
                "unusual on the low side relative to "
                "its manufacturing lot."
            )

        else:
            severity = Severity.INFO
            finding_type = "lot_baseline_pass"
            summary = (
                "Component early leakage behaviour is "
                "statistically consistent with its "
                "manufacturing lot."
            )

        evidence = [
            (
                f"Component leakage at 24h: "
                f"{component_value:.2f} uA."
            ),
            (
                f"Lot median leakage at 24h: "
                f"{lot_median:.2f} uA."
            ),
            f"Lot MAD: {lot_mad:.2f} uA.",
            (
                f"Robust z-score: "
                f"{robust_z_score:.2f}."
            ),
            (
                f"Percentile rank: "
                f"{percentile * 100:.1f}%."
            ),
            (
                f"Lot evidence level: "
                f"{evidence_level.value}."
            ),
            (
                f"Isolation Forest anomaly score: "
                f"{isolation_score:.4f}."
            ),
            (
                "Isolation Forest classified the early "
                f"behaviour as "
                f"{'anomalous' if isolation_anomaly else 'typical'}."
            ),
        ]

        metadata = {
            "lot_id": lot_context.lot_id,
            "lot_population_size": len(
                lot_24h_values
            ),
            "component_value": component_value,
            "lot_median": lot_median,
            "lot_mad": lot_mad,
            "robust_z_score": robust_z_score,
            "percentile": percentile,
            "robust_anomaly_score": (
                robust_anomaly_score
            ),
            "deviation_direction": (
                deviation_direction.value
            ),
            "evidence_level": (
                evidence_level.value
            ),
            "is_outlier": is_outlier,
            "isolation_score": isolation_score,
            "isolation_anomaly": (
                isolation_anomaly
            ),
        }

        finding = Finding(
            agent=self.name,
            component_id=state.component_id,
            finding_type=finding_type,
            severity=severity,
            summary=summary,
            evidence=evidence,
            metadata=metadata,
        )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            **metadata,

            # Preserve this for compatibility, but it
            # now means "no material lot-relative signal",
            # not merely "not a 3.5-sigma outlier".
            "passed": (
                not high_side_evidence
                and not isolation_anomaly
            ),
        }

        return state