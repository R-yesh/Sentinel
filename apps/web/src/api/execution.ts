import { AGENT_IDS, isRecord, type AgentId } from './investigation';

export interface AgentExecution {
  agent: AgentId;
  status: 'completed' | 'failed' | 'cancelled' | 'not_executed';
  started_at: string | null;
  completed_at: string | null;
  start_offset_ms: number | null;
  end_offset_ms: number | null;
  duration_ms: number | null;
}
export interface WorkflowExecution { total_duration_ms: number; agents: AgentExecution[] }
const nonnegative = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n) && n >= 0;

/** Reject unusable telemetry without rejecting the analytical response. */
export function parseExecution(value: unknown): WorkflowExecution | null {
  if (!isRecord(value) || !nonnegative(value.total_duration_ms) || !Array.isArray(value.agents) || value.agents.length !== AGENT_IDS.length) return null;
  const seen = new Set<string>();
  for (const row of value.agents) {
    if (!isRecord(row) || !AGENT_IDS.includes(row.agent as AgentId) || seen.has(row.agent as string)) return null;
    seen.add(row.agent as string);
    if (row.status === 'not_executed') {
      if ([row.started_at, row.completed_at, row.start_offset_ms, row.end_offset_ms, row.duration_ms].some((v) => v !== null)) return null;
    } else {
      if (!['completed', 'failed', 'cancelled'].includes(row.status as string) || !nonnegative(row.start_offset_ms) || !nonnegative(row.end_offset_ms) || !nonnegative(row.duration_ms)) return null;
      if (row.end_offset_ms < row.start_offset_ms || row.end_offset_ms > value.total_duration_ms + 0.01 || Math.abs(row.end_offset_ms - row.start_offset_ms - row.duration_ms) > 0.01) return null;
      if (![row.started_at, row.completed_at].every((stamp) => typeof stamp === 'string' && Number.isFinite(Date.parse(stamp)))) return null;
    }
  }
  return value as unknown as WorkflowExecution;
}

export function duration(ms: number | null | undefined): string {
  if (ms == null || !nonnegative(ms)) return 'Timing unavailable';
  if (ms < 1) return `${ms.toFixed(2)} ms`;
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}
