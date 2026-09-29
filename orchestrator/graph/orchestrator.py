import asyncio
from orchestrator.graph.execution import ExecutionRecorder

from agents.data_forensics.agent import DataForensicsAgent
from agents.drift_intelligence.agent import DriftIntelligenceAgent
from agents.lot_intelligence.agent import LotIntelligenceAgent
from agents.latent_defect.agent import LatentDefectAgent
from agents.adversarial_qa.agent import AdversarialQAAgent
from agents.reliability_judge.agent import ReliabilityJudgeAgent
from agents.explanation.agent import ExplanationAgent

from shared.schemas.workflow import WorkflowState, WorkflowStatus


class SentinelOrchestrator:
    def __init__(self):
        self.data_forensics = DataForensicsAgent()
        self.lot_intelligence = LotIntelligenceAgent()
        self.drift_intelligence = DriftIntelligenceAgent()
        self.latent_defect = LatentDefectAgent()
        self.adversarial_qa = AdversarialQAAgent()
        self.reliability_judge = ReliabilityJudgeAgent()
        self.explanation = ExplanationAgent()

    async def run(self, state: WorkflowState, *, execution: ExecutionRecorder | None = None) -> WorkflowState:
        execution = execution if execution is not None else ExecutionRecorder()
        execution.begin()
        try:
            return await self._run(state, execution)
        finally:
            execution.finish()

    async def _run(self, state: WorkflowState, execution: ExecutionRecorder) -> WorkflowState:
        state.status = WorkflowStatus.RUNNING

        # Step 1: Validate the incoming data first.
        state = await execution.execute('data_forensics', self.data_forensics, state)

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
            execution.execute('lot_intelligence', self.lot_intelligence, lot_state),
            execution.execute('drift_intelligence', self.drift_intelligence, drift_state),
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

        state = await execution.execute('latent_defect', self.latent_defect, state)
        state = await execution.execute('adversarial_qa', self.adversarial_qa, state)
        state = await execution.execute('reliability_judge', self.reliability_judge, state)
        state = await execution.execute('explanation', self.explanation, state)

        return state
