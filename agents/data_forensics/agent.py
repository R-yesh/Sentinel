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

    async def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:
        # -----------------------------------------
        # Component measurement validation
        # -----------------------------------------

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
                invalid_numeric_fields.append(
                    field
                )
                continue

            if not math.isfinite(value):
                invalid_numeric_fields.append(
                    field
                )

        physically_invalid_fields = []

        for field in REQUIRED_MEASUREMENTS:
            value = state.raw_data.get(field)

            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value < 0
            ):
                physically_invalid_fields.append(
                    field
                )

        # -----------------------------------------
        # Lot-context measurement validation
        # -----------------------------------------

        missing_lot_measurements = []
        invalid_lot_measurements = []
        physically_invalid_lot_measurements = []

        lot_context = state.lot_context

        if lot_context is not None:
            lot_populations = {
                "leakage_0h_population": (
                    lot_context.leakage_0h_population
                ),
                "leakage_24h_population": (
                    lot_context.leakage_24h_population
                ),
            }

            for (
                population_name,
                population,
            ) in lot_populations.items():
                for index, value in enumerate(
                    population
                ):
                    if value is None:
                        missing_lot_measurements.append(
                            {
                                "field": population_name,
                                "index": index,
                            }
                        )
                        continue

                    if (
                        not isinstance(
                            value,
                            (int, float),
                        )
                        or isinstance(value, bool)
                    ):
                        invalid_lot_measurements.append(
                            {
                                "field": population_name,
                                "index": index,
                            }
                        )
                        continue

                    if not math.isfinite(value):
                        invalid_lot_measurements.append(
                            {
                                "field": population_name,
                                "index": index,
                            }
                        )
                        continue

                    if value < 0:
                        (
                            physically_invalid_lot_measurements
                            .append(
                                {
                                    "field": population_name,
                                    "index": index,
                                }
                            )
                        )

        # -----------------------------------------
        # Combined validation result
        # -----------------------------------------

        has_errors = bool(
            missing_fields
            or invalid_numeric_fields
            or physically_invalid_fields
            or missing_lot_measurements
            or invalid_lot_measurements
            or physically_invalid_lot_measurements
        )

        if has_errors:
            evidence = []

            evidence.extend(
                (
                    f"Required measurement '{field}' "
                    f"is missing."
                )
                for field in missing_fields
            )

            evidence.extend(
                (
                    f"Measurement '{field}' is not "
                    f"a valid finite numeric value."
                )
                for field in invalid_numeric_fields
            )

            evidence.extend(
                (
                    f"Measurement '{field}' contains "
                    f"a physically invalid negative "
                    f"leakage value."
                )
                for field in physically_invalid_fields
            )

            evidence.extend(
                (
                    f"Lot measurement "
                    f"'{item['field']}' at index "
                    f"{item['index']} is missing."
                )
                for item in missing_lot_measurements
            )

            evidence.extend(
                (
                    f"Lot measurement "
                    f"'{item['field']}' at index "
                    f"{item['index']} is not a valid "
                    f"finite numeric value."
                )
                for item in invalid_lot_measurements
            )

            evidence.extend(
                (
                    f"Lot measurement "
                    f"'{item['field']}' at index "
                    f"{item['index']} contains a "
                    f"physically invalid negative "
                    f"leakage value."
                )
                for item in (
                    physically_invalid_lot_measurements
                )
            )

            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="invalid_burnin_data",
                severity=Severity.HIGH,
                summary=(
                    "Invalid burn-in measurement "
                    "data were detected."
                ),
                evidence=evidence,
                metadata={
                    "missing_fields": (
                        missing_fields
                    ),
                    "invalid_numeric_fields": (
                        invalid_numeric_fields
                    ),
                    "physically_invalid_fields": (
                        physically_invalid_fields
                    ),
                    "missing_lot_measurements": (
                        missing_lot_measurements
                    ),
                    "invalid_lot_measurements": (
                        invalid_lot_measurements
                    ),
                    (
                        "physically_invalid_"
                        "lot_measurements"
                    ): (
                        physically_invalid_lot_measurements
                    ),
                },
            )

        else:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="data_quality_pass",
                severity=Severity.INFO,
                summary=(
                    "Burn-in measurement data "
                    "passed validation."
                ),
                evidence=[
                    (
                        "All available required "
                        "measurements are present, "
                        "finite, numeric, and "
                        "physically valid."
                    )
                ],
            )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "missing_fields": missing_fields,
            "invalid_numeric_fields": (
                invalid_numeric_fields
            ),
            "physically_invalid_fields": (
                physically_invalid_fields
            ),
            "missing_lot_measurements": (
                missing_lot_measurements
            ),
            "invalid_lot_measurements": (
                invalid_lot_measurements
            ),
            "physically_invalid_lot_measurements": (
                physically_invalid_lot_measurements
            ),
            "passed": not has_errors,
        }

        return state