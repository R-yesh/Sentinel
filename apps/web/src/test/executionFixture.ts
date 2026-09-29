import { AGENT_IDS } from '../api/investigation';
import type { WorkflowExecution } from '../api/execution';

// Test-only elapsed intervals: Drift and Lot overlap but finish at different times.
export function executionFixture(): WorkflowExecution {
  const intervals = [[0, 20], [25, 180], [26, 280], [290, 400], [410, 2410], [2420, 3400], [3410, 4000]];
  return { total_duration_ms: 4010, agents: AGENT_IDS.map((agent, i) => ({ agent, status: 'completed',
    started_at: '2026-09-29T00:00:00+00:00', completed_at: '2026-09-29T00:00:04+00:00',
    start_offset_ms: intervals[i][0], end_offset_ms: intervals[i][1], duration_ms: intervals[i][1] - intervals[i][0],
  })) };
}
