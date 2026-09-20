import math

from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState
from agents.base import BaseAgent

REQUIRED_MEASUREMENTS = [
    "leakage_0h",
    "leakage_24h",
]

class DataForensicsAgent(BaseAgent):
    name = "data_forensics"

    async def run(self, state: WorkflowState) -> WorkflowState:
        missing_fields = [
            field
            for field in REQUIRED_MEASUREMENTS
            if (
                field not in state.raw_data
                or state.raw_data[field] is None
            )
        ]

        invalid_numeric_fields = []

        for field in REQUIRED_MEASUREMENTS:
            value = state.raw_data.get(field)

            if value is None:
                continue

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                invalid_numeric_fields.append(field)
                continue

            if not math.isfinite(value):
                invalid_numeric_fields.append(field)

        physically_invalid_fields = []

        for field in REQUIRED_MEASUREMENTS:
            value = state.raw_data.get(field)

            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value < 0
            ):
                physically_invalid_fields.append(field)
        
        has_errors = bool(
            missing_fields
            or invalid_numeric_fields
            or physically_invalid_fields
        )

        if has_errors:
            evidence = []

            evidence.extend(
                f"Required measurement '{field}' is missing."
                for field in missing_fields
            )

            evidence.extend(
                f"Measurement '{field}' is not a valid finite numeric value."
                for field in invalid_numeric_fields
            )

            evidence.extend(
                f"Measurement '{field}' contains a physically invalid negative leakage value."
                for field in physically_invalid_fields
            )

            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="invalid_burnin_data",
                severity=Severity.HIGH,
                score=1.0,
                confidence=1.0,
                summary=(
                    "Invalid burn-in measurement data were detected."
                ),
                evidence=evidence,
                metadata={
                    "missing_fields": missing_fields,
                    "invalid_numeric_fields": invalid_numeric_fields,
                    "physically_invalid_fields": physically_invalid_fields,
                },
            )
        else:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="data_quality_pass",
                severity=Severity.INFO,
                score=0.0,
                confidence=1.0,
                summary=(
                    "Burn-in measurement data passed validation."
                ),
                evidence=[
                    (
                        "All required measurements are present, "
                        "finite, numeric, and physically valid."
                    )
                ],
            )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "missing_fields": missing_fields,
            "invalid_numeric_fields": invalid_numeric_fields,
            "physically_invalid_fields": physically_invalid_fields,
            "passed": not has_errors,
        }

        return state