import { ArrowDown, Check, Circle, Database, GitBranch, Pause, Play, RotateCcw, SkipForward, TriangleAlert } from 'lucide-react';
import { type AgentId, type WorkflowState } from '../../api/investigation';
import { duration, type WorkflowExecution } from '../../api/execution';
import { AGENTS, hasEvidence, needsAttention, STAGES } from './presentation';
import { ExecutionSummary } from './ExecutionSummary';
import { useExecutionReplay } from './replay';

export function WorkflowGraph({ workflow, execution, running, selected, onSelect, onDisposition }: {
  workflow?: WorkflowState; execution?: WorkflowExecution | null; running: boolean;
  selected: AgentId | null; onSelect: (agent: AgentId) => void; onDisposition?: () => void;
}) {
  const replay = useExecutionReplay(execution);
  const rows = replay.timeline?.agents;
  const completed = rows?.filter((r) => r.end !== null && r.end <= replay.cursor).map((r) => r.agent) ?? [];
  const active = rows?.filter((r) => r.start !== null && r.end !== null && r.start <= replay.cursor && replay.cursor < r.end).map((r) => r.agent) ?? [];
  const evidenceCount = workflow?.findings.filter((f) => replay.complete || completed.includes(f.agent as AgentId)).length ?? 0;
  return <section className={`panel workflow-panel ${replay.playing ? '' : 'replay-paused'}`} aria-labelledby="workflow-heading">
    <div className="workflow-panel-header"><div><span className="eyebrow">SENTINEL / EXECUTION REPLAY</span><h2 id="workflow-heading">One component. Shared evidence.</h2></div><GitBranch size={22} strokeWidth={1.3} /></div>
    <div className="workflow-explainer"><span className="status-dot" /><p>{workflow ? 'Completed response · inspect any agent. Replay is retrospective, never live progress.' : running ? 'Request running · individual agent progress is not available.' : 'Pipeline topology · ready for an investigation.'}</p></div>
    {workflow && <ExecutionSummary execution={execution} />}
    <div className="replay-controls"><span>{execution ? 'Execution replay · normalized visual time; labels show real duration' : 'Timing replay requires valid execution telemetry'}</span>{replay.timeline && <div className="replay-buttons">
      <button className="text-button" onClick={replay.replay}><Play size={13} />Replay</button>
      {!replay.complete && <button className="text-button" onClick={replay.toggle}>{replay.playing ? <Pause size={13} /> : <Play size={13} />}{replay.playing ? 'Pause' : 'Resume'}</button>}
      <button className="text-button" onClick={replay.reset}><RotateCcw size={13} />Reset</button>
      <button className="text-button" onClick={replay.skip}><SkipForward size={13} />Skip to result</button>
    </div>}</div>
    <div className="workflow-canvas" aria-label="Agent workflow">
      <div className="workflow-source">OBSERVED 0h / 24h → WORKFLOW STATE</div>
      {STAGES.map((agents, index) => <div key={index} className={`flow-stage ${agents.length > 1 ? 'parallel-stage' : ''} ${agents.some((id) => active.includes(id)) ? 'replay-stage' : ''}`}>
        <div className={`flow-connector ${index === 1 ? 'branch-connector' : index === 2 ? 'merge-connector' : ''}`} aria-hidden="true"><ArrowDown size={13} /><span className="evidence-trace" /></div>
        {index === 1 && <span className="parallel-label">INDEPENDENT ANALYSES · SEPARATE STATE COPIES</span>}
        <div className="flow-nodes">{agents.map((id) => {
          const record = rows?.find((r) => r.agent === id);
          const available = !!workflow && hasEvidence(workflow, id);
          const output = workflow?.agent_outputs[id];
          const guardrail = (id === 'data_forensics' && output?.passed === false) || (['lot_intelligence', 'drift_intelligence'].includes(id) && typeof output?.reason === 'string') || output?.assessment === 'INSUFFICIENT_EVIDENCE';
          const attention = !!workflow && (guardrail || needsAttention(workflow, id));
          const isActive = active.includes(id);
          const before = record?.start != null && replay.cursor < record.start;
          const label = !workflow ? 'Awaiting response' : !record ? available ? 'Evidence returned' : 'Execution unknown' : record.status === 'not_executed' ? 'Not executed' : before ? 'Replay pending' : isActive ? 'Replay active' : record.status !== 'completed' ? record.status : attention ? 'Completed · attention' : 'Completed';
          return <button key={id} className={`agent-node ${available ? 'has-evidence' : ''} ${attention ? 'has-concern' : ''} ${isActive ? 'replay-active' : ''} ${selected === id ? 'inspected' : ''}`} disabled={!workflow} onClick={() => onSelect(id)} aria-label={`Inspect ${AGENTS[id].name}`} aria-pressed={selected === id}>
            <span className="agent-node-top"><span className="node-number">{index === 1 ? id === 'drift_intelligence' ? '02A' : '02B' : `0${index + 1}`}</span><span className="node-status">{record?.status === 'completed' && !before && !isActive ? attention ? <TriangleAlert size={11} /> : <Check size={11} /> : <Circle size={9} />}{label}</span></span>
            <strong>{AGENTS[id].name}</strong><span className="node-description">{AGENTS[id].description}</span>
            {workflow && <span className="node-duration">{record?.status === 'not_executed' ? '—' : duration(record?.duration_ms)}<small> {record?.status === 'not_executed' ? 'no execution' : 'measured elapsed'}</small></span>}
          </button>;
        })}</div>
      </div>)}
      <div className="flow-connector" aria-hidden="true"><ArrowDown size={13} /></div>
      <button className={`workflow-disposition disposition-${workflow?.final_decision?.toLowerCase() ?? 'none'}`} disabled={!workflow} onClick={onDisposition}><span className="tiny-label">RETURNED DISPOSITION{!replay.complete ? ' · REPLAY NOT FINISHED' : ''}</span><strong>{workflow?.final_decision ?? 'No decision issued'}</strong><span>Open engineering explanation</span></button>
    </div>
    <div className={`state-packet ${active.length ? 'packet-replaying' : ''}`}><Database size={20} /><div><span className="tiny-label">SHARED WORKFLOW STATE / EVIDENCE</span><strong>{workflow ? `${evidenceCount} findings ${replay.complete ? 'returned' : 'from completed replay intervals'}` : 'Observed input → findings → disposition'}</strong><p>{!workflow ? 'Evidence appears after the investigation returns' : active.length ? active.map((id) => AGENTS[id].name).join(' + ') : replay.complete ? 'Returned state available for inspection' : 'Replay paused or between agent intervals'}</p></div></div>

  </section>;
}
