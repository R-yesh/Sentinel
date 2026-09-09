import asyncio

from agents.data_forensics.agent import DataForensicsAgent
from agents.drift_intelligence.agent import DriftIntelligenceAgent
from agents.lot_intelligence.agent import LotIntelligenceAgent
from agents.latent_defect.agent import LatentDefectAgent

from shared.schemas.workflow import WorkflowState, WorkflowStatus


class SentinelOrchestrator:
    def __init__(self):
        self.data_forensics = DataForensicsAgent()
        self.lot_intelligence = LotIntelligenceAgent()
        self.drift_intelligence = DriftIntelligenceAgent()
        self.latent_defect = LatentDefectAgent()

    async def run(self, state: WorkflowState) -> WorkflowState:
        state.status = WorkflowStatus.RUNNING

        # Step 1: Validate the incoming data first.
        state = await self.data_forensics.run(state)

        data_quality = state.agent_outputs.get(
            "data_forensics",
            {},
        )

        if not data_quality.get("passed", False):
            state.status = WorkflowStatus.NEEDS_REVIEW
            return state

        # Remember how many findings existed before branching.
        baseline_finding_count = len(state.findings)

        # Give each parallel agent its own independent copy.
        lot_state = state.model_copy(deep=True)
        drift_state = state.model_copy(deep=True)

        # Step 2: Run independent analyses concurrently.
        lot_result, drift_result = await asyncio.gather(
            self.lot_intelligence.run(lot_state),
            self.drift_intelligence.run(drift_state),
        )

        # Step 3: Merge only the findings created by each branch.
        lot_findings = lot_result.findings[baseline_finding_count:]
        drift_findings = drift_result.findings[baseline_finding_count:]

        state.findings.extend(lot_findings)
        state.findings.extend(drift_findings)

        # Merge their structured outputs.
        state.agent_outputs["lot_intelligence"] = (
            lot_result.agent_outputs["lot_intelligence"]
        )

        state.agent_outputs["drift_intelligence"] = (
            drift_result.agent_outputs["drift_intelligence"]
        )

        state = await self.latent_defect.run(state)

        return state