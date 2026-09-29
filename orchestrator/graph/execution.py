"""Best-effort timing. Never passed to agents or used for analytical decisions."""
import asyncio
from datetime import datetime, timezone
from time import perf_counter

from shared.schemas.execution import AGENT_NAMES, WorkflowExecution


class ExecutionRecorder:
    def __init__(self):
        self.origin = None
        self.total = None
        self.records = {}
        self.valid = True

    def _record(self, event, name=None, status=None):
        # A broken clock/serialization path must not change agent execution.
        try:
            tick = perf_counter()
            stamp = datetime.now(timezone.utc).isoformat()
            if event == 'begin':
                self.origin = tick
            elif event == 'finish':
                self.total = (tick - self.origin) * 1000
            elif event == 'start':
                self.records[name] = dict(agent=name, started_at=stamp,
                                          start_offset_ms=(tick - self.origin) * 1000)
            else:
                row = self.records[name]
                end = (tick - self.origin) * 1000
                row.update(status=status, completed_at=stamp, end_offset_ms=end,
                           duration_ms=end - row['start_offset_ms'])
        except Exception:
            self.valid = False

    def begin(self):
        self._record('begin')

    def finish(self):
        self._record('finish')

    async def execute(self, name, agent, state):
        self._record('start', name)
        status = 'failed'
        try:
            result = await agent.run(state)
            status = 'completed'
            return result
        except asyncio.CancelledError:
            status = 'cancelled'
            raise
        finally:
            self._record('end', name, status)

    def snapshot(self):
        try:
            if not self.valid:
                return None
            return WorkflowExecution(total_duration_ms=self.total, agents=[
                self.records.get(name, dict(agent=name, status='not_executed'))
                for name in AGENT_NAMES
            ])
        except Exception:
            return None
