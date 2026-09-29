import { duration, type WorkflowExecution } from '../../api/execution';
import { AGENTS } from './presentation';

export function ExecutionSummary({ execution }: { execution?: WorkflowExecution | null }) {
  if (!execution) return <p className="execution-unavailable">Execution timing unavailable. Returned evidence remains inspectable; no timing replay is inferred.</p>;
  const executed = execution.agents.filter((a) => a.status !== 'not_executed');
  const slowest = executed.reduce<(typeof executed)[number] | undefined>((max, a) => !max || a.duration_ms! > max.duration_ms! ? a : max, undefined);
  const drift = executed.find((a) => a.agent === 'drift_intelligence');
  const lot = executed.find((a) => a.agent === 'lot_intelligence');
  const overlap = drift && lot ? Math.max(0, Math.min(drift.end_offset_ms!, lot.end_offset_ms!) - Math.max(drift.start_offset_ms!, lot.start_offset_ms!)) : null;
  return <div className="execution-summary" aria-label="Measured execution summary">
    <dl><div><dt>Workflow duration</dt><dd>{duration(execution.total_duration_ms)}</dd></div><div><dt>Agents executed</dt><dd>{executed.length} / 7</dd></div><div><dt>Slowest agent</dt><dd>{slowest ? AGENTS[slowest.agent].name : 'None'}</dd><small>{duration(slowest?.duration_ms)}</small></div></dl>
    <p>Total agent elapsed time includes computation and waits; it is not model inference time alone.</p>
    {drift && lot ? <div className="branch-timing"><strong>Independent branches · asyncio.gather</strong><span>Drift {duration(drift.duration_ms)} · Lot {duration(lot.duration_ms)}</span><span>Measured overlap: {duration(overlap)}</span><p>{overlap ? 'Replay preserves the recorded overlapping intervals.' : 'No interval overlap recorded. Synchronous work can occupy the event loop despite concurrent scheduling.'}</p></div> : <p>Branch timing unavailable: both analyses did not execute.</p>}
  </div>;
}
