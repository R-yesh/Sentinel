import { useEffect, useState } from 'react';
import { ArrowDown, Check, Circle, Database, GitBranch, Play, ShieldCheck, SkipForward, TriangleAlert } from 'lucide-react';
import { type AgentId, type WorkflowState } from '../../api/investigation';
import { AGENTS, contributedAgents, hasEvidence, needsAttention, STAGES } from './presentation';

export function WorkflowGraph({ workflow, running, selected, onSelect }: {
  workflow?: WorkflowState; running: boolean; selected: AgentId | null; onSelect: (agent: AgentId) => void;
}) {
  const [stage, setStage] = useState(STAGES.length);
  const [replay, setReplay] = useState(0);
  useEffect(() => {
    if (!workflow || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { setStage(STAGES.length); return; }
    setStage(0);
    const interval = window.setInterval(() => setStage((current) => {
      if (current >= STAGES.length - 1) { window.clearInterval(interval); return STAGES.length; }
      return current + 1;
    }), 300);
    return () => window.clearInterval(interval);
  }, [workflow, replay]);
  const playing = !!workflow && stage < STAGES.length;
  const focusIds = STAGES.slice(0, stage + 1).flat();
  const count = workflow ? workflow.findings.filter((finding) => focusIds.includes(finding.agent as AgentId)).length : 0;
  return <section className="panel workflow-panel" aria-labelledby="workflow-heading">
    <div className="workflow-panel-header"><div><span className="eyebrow">SENTINEL / EVIDENCE PIPELINE</span><h2 id="workflow-heading">One component. Shared evidence.</h2></div><GitBranch size={22} strokeWidth={1.3} /></div>
    <div className="workflow-explainer"><span className="status-dot" /><p>{workflow ? 'Returned workflow · select any available agent to inspect its evidence.' : running ? 'Request running · individual agent progress is not available.' : 'Pipeline topology · ready for an investigation.'}</p></div>
    <div className="workflow-canvas" aria-label="Agent workflow">
      {STAGES.map((agents, index) => <div key={index} className={`flow-stage ${agents.length > 1 ? 'parallel-stage' : ''} ${stage === index && playing ? 'replay-stage' : ''}`}>
        {index > 0 && <div className={`flow-connector ${index === 1 ? 'branch-connector' : index === 2 ? 'merge-connector' : ''}`} aria-hidden="true"><ArrowDown size={13} /></div>}
        {index === 1 && <span className="parallel-label">INDEPENDENT ANALYSES · SEPARATE STATE COPIES</span>}
        <div className="flow-nodes">{agents.map((id) => {
          const available = !!workflow && hasEvidence(workflow, id);
          const attention = !!workflow && needsAttention(workflow, id);
          const active = playing && stage === index && available;
          const label = available ? active ? 'Replay focus' : attention ? 'Attention' : 'Completed' : workflow ? 'No output returned' : 'Awaiting response';
          return <button key={id} className={`agent-node ${available ? 'has-evidence' : ''} ${attention ? 'has-concern' : ''} ${active ? 'replay-active' : ''} ${available && selected === id ? 'inspected' : ''}`} disabled={!available} onClick={() => onSelect(id)} aria-label={`Inspect ${AGENTS[id].name}`} aria-pressed={available && selected === id}>
            <span className="agent-node-top"><span className="node-number">{index === 1 ? id === 'drift_intelligence' ? '02A' : '02B' : `0${index + 1}`}</span><span className="node-status">{available ? attention ? <TriangleAlert size={11} /> : <Check size={11} /> : <Circle size={9} />}{label}</span></span>
            <strong>{AGENTS[id].name}</strong><span className="node-description">{AGENTS[id].description}</span>
          </button>;
        })}</div>
      </div>)}
    </div>
    <div className={`state-packet ${playing ? 'packet-replaying' : ''}`}><Database size={20} /><div><span className="tiny-label">SHARED WORKFLOW STATE</span><strong>{workflow ? `${playing ? count : workflow.findings.length} findings ${playing ? 'highlighted in replay' : 'returned'}` : 'Observed input → findings → disposition'}</strong><p>{workflow ? `${contributedAgents(workflow).length} agents contributed · ${workflow.component_id}` : 'Evidence accumulates in one component investigation.'}</p></div>{workflow && <ShieldCheck size={18} />}</div>
    <div className="replay-controls"><span>{workflow ? playing ? 'Presentation replay · response already received' : 'Replay shows returned evidence, not live progress' : 'No per-agent progress is inferred'}</span>{workflow && <button className="text-button" onClick={() => playing ? setStage(STAGES.length) : setReplay((value) => value + 1)}>{playing ? <SkipForward size={13} /> : <Play size={13} />}{playing ? 'Skip replay' : 'Replay'}</button>}</div>
  </section>;
}
