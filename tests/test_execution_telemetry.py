import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from orchestrator.graph.execution import ExecutionRecorder
from orchestrator.graph.orchestrator import SentinelOrchestrator
from shared.schemas.execution import AGENT_NAMES
from shared.schemas.workflow import WorkflowState
from test_api_integration import local_inference  # Controlled model/LLM fixture; no network.


def state():
    return WorkflowState(workflow_id='timing', component_id='C', raw_data={'leakage_0h': 10, 'leakage_24h': 11})


def pipeline(stop=False, fail=None):
    orchestrator = SentinelOrchestrator()
    for name in AGENT_NAMES:
        async def run(s, name=name):
            await asyncio.sleep(.01 if name in ('drift_intelligence', 'lot_intelligence') else 0)
            if name == fail:
                raise ValueError('agent failure')
            s.agent_outputs[name] = {'passed': not stop if name == 'data_forensics' else True}
            if name == 'reliability_judge':
                s.final_decision = 'PASS'
            return s
        setattr(orchestrator, name, SimpleNamespace(run=run))
    return orchestrator


@pytest.mark.asyncio
async def test_execution_records_order_and_genuine_overlap():
    recorder = ExecutionRecorder()
    await pipeline().run(state(), execution=recorder)
    result = recorder.snapshot()
    rows = {r.agent: r for r in result.agents}
    assert len(rows) == 7
    assert all(r.status == 'completed' and r.duration_ms >= 0 and r.started_at and r.completed_at for r in rows.values())
    drift, lot = rows['drift_intelligence'], rows['lot_intelligence']
    assert max(drift.start_offset_ms, lot.start_offset_ms) < min(drift.end_offset_ms, lot.end_offset_ms)
    assert rows['data_forensics'].end_offset_ms <= min(drift.start_offset_ms, lot.start_offset_ms)
    assert rows['latent_defect'].start_offset_ms >= max(drift.end_offset_ms, lot.end_offset_ms)
    for first, second in zip(('latent_defect', 'adversarial_qa', 'reliability_judge'), ('adversarial_qa', 'reliability_judge', 'explanation')):
        assert rows[first].end_offset_ms <= rows[second].start_offset_ms
    assert result.total_duration_ms >= max(r.end_offset_ms for r in rows.values())


@pytest.mark.asyncio
async def test_validation_stop_never_fabricates_later_executions():
    recorder = ExecutionRecorder()
    result = await pipeline(stop=True).run(state(), execution=recorder)
    assert result.final_decision is None
    assert recorder.snapshot().agents[0].status == 'completed'
    assert all(r.status == 'not_executed' and r.duration_ms is None for r in recorder.snapshot().agents[1:])


@pytest.mark.asyncio
async def test_failures_propagate_without_fabricated_completion():
    recorder = ExecutionRecorder()
    with pytest.raises(ValueError, match='agent failure'):
        await pipeline(fail='latent_defect').run(state(), execution=recorder)
    rows = {r.agent: r for r in recorder.snapshot().agents}
    assert rows['latent_defect'].status == 'failed'
    assert rows['reliability_judge'].status == 'not_executed'


@pytest.mark.asyncio
async def test_bad_clock_cannot_change_analytical_state(monkeypatch):
    baseline = await pipeline().run(state())
    def broken_clock():
        raise RuntimeError('clock unavailable')
    monkeypatch.setattr('orchestrator.graph.execution.perf_counter', broken_clock)
    recorder = ExecutionRecorder()
    result = await pipeline().run(state(), execution=recorder)
    assert result.model_dump() == baseline.model_dump()
    assert recorder.snapshot() is None


def test_api_telemetry_with_existing_analytical_agents(local_inference, monkeypatch):
    with TestClient(app) as client:
        selection = {'dataset_id': 'synthetic-burnin', 'component_id': 'C0001'}
        measured = client.post('/api/v1/investigations', json=selection)
        assert measured.status_code == 200
        data = measured.json()
        assert len(data['workflow_execution']['agents']) == 7
        assert all(r['status'] == 'completed' for r in data['workflow_execution']['agents'])
        # Bypass observation only; retain identical agents, orchestration and inputs.
        async def unmeasured(self, name, agent, s):
            return await agent.run(s)
        monkeypatch.setattr(ExecutionRecorder, 'execute', unmeasured)
        unmeasured_data = client.post('/api/v1/investigations', json=selection).json()
        a, b = data['workflow'], unmeasured_data['workflow']
        a.pop('workflow_id'); b.pop('workflow_id')
        assert a == b
