from shared.schemas.findings import Finding, Severity
from shared.schemas.workflow import WorkflowState
from agents.base import BaseAgent


class DataForensicsAgent(BaseAgent):
    name = "data_forensics"

    async def run(self, state: WorkflowState) -> WorkflowState:
        missing_fields = [
            key
            for key, value in state.raw_data.items()
            if value is None
        ]

        if missing_fields:
            finding = Finding(
                agent=self.name,
                component_id=state.component_id,
                finding_type="missing_measurements",
                severity=Severity.HIGH,
                score=0.8,
                confidence=1.0,
                summary="Missing measurements were detected in the burn-in data.",
                evidence=[
                    f"Missing value detected for '{field}'."
                    for field in missing_fields
                ],
                metadata={
                    "missing_fields": missing_fields,
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
                summary="No missing measurements were detected.",
                evidence=[
                    "All supplied measurement fields contain values."
                ],
            )

        state.findings.append(finding)

        state.agent_outputs[self.name] = {
            "missing_fields": missing_fields,
            "passed": len(missing_fields) == 0,
        }

        return state