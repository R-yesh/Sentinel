import { useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, CircleAlert, LoaderCircle, SearchCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AgentId, InvestigationSelection } from '../../api/investigation';
import { useInvestigationSession } from './InvestigationSession';
import { AgentInspector } from './AgentInspector';
import { Disposition } from './Disposition';
import { InputContext } from './InputContext';
import { WorkflowGraph } from './WorkflowGraph';
import { hasEvidence } from './presentation';

export function InvestigationWorkspace({ selection }: { selection: InvestigationSelection }) {
  const { run: current, start } = useInvestigationSession();
  const run = current?.selection.dataset_id === selection.dataset_id && current.selection.component_id === selection.component_id ? current : null;
  const workflow = run?.status === 'success' ? run.result.workflow : undefined;
  const [agent, setAgent] = useState<AgentId>('data_forensics');
  const [view, setView] = useState<'disposition' | 'agent'>('disposition');
  const details = useRef<HTMLDivElement>(null);
  const execute = () => { setView('disposition'); start(selection, run?.observed); };
  const back = `/dataset?${new URLSearchParams({ component: selection.component_id })}`;
  return <div className="workspace-page investigation-page">
    <div className="page-heading"><div><span className="eyebrow">COMPONENT INVESTIGATION / SENTINEL</span><h1>Follow the evidence<span className="heading-dot">.</span></h1><p>Specialized analysis. Shared state. An auditable reliability disposition.</p></div><Link to={back} className="button secondary"><ArrowLeft size={14} />Back to dataset</Link></div>
    <InputContext selection={selection} observed={run?.observed} workflow={workflow} />
    {!run && <div className="run-banner ready-banner"><SearchCheck size={23} /><div><strong>Ready to investigate {selection.component_id}</strong><p>This selection has no active result in this tab. Start the existing Sentinel pipeline.</p></div><button className="button primary" onClick={execute}>Run investigation<ArrowRight size={15} /></button></div>}
    {run?.status === 'running' && <div className="run-banner" role="status"><LoaderCircle className="spinner" size={24} /><div><strong>Sentinel is investigating {selection.component_id}</strong><p>The API returns the whole workflow at once. This may take several minutes; individual agent progress is not available.</p><small>Leaving this screen does not cancel server execution. Return to Analysis to view the current request.</small></div></div>}
    {run?.status === 'error' && <div className="run-banner error-banner" role="alert"><CircleAlert size={25} /><div><strong>Investigation could not be displayed</strong><p>{run.message}</p><small>No decision is inferred. Retry starts a new investigation; a timed-out request may still finish on the server.</small></div><button className="button secondary" onClick={execute}>Retry investigation</button></div>}
    {workflow && <div className={`result-strip disposition-${workflow.final_decision?.toLowerCase() ?? 'none'}`}>
      <div><span className="tiny-label">RETURNED DISPOSITION</span><strong>{workflow.final_decision ?? 'No decision issued'}</strong></div><div><span className="tiny-label">WORKFLOW ID</span><code>{workflow.workflow_id}</code></div><div><span className="tiny-label">WORKFLOW STATUS</span><span>{workflow.status}</span></div>
    </div>}
    {run?.status === 'success' && run.result.issues.length > 0 && <div className="response-notes" role="alert"><strong>Response completeness notes</strong><ul>{run.result.issues.map((issue) => <li key={issue}>{issue}</li>)}</ul></div>}
    <div className="investigation-grid">
      <WorkflowGraph key={workflow?.workflow_id ?? 'pending'} workflow={workflow} running={run?.status === 'running'} selected={view === 'agent' ? agent : null} onSelect={(id) => { setAgent(id); setView('agent'); if (window.matchMedia?.('(max-width: 1000px)').matches) details.current?.scrollIntoView({ block: 'start' }); }} />
      <div ref={details} className="investigation-detail-column">
        {workflow ? <>
          <div className="result-view-switch" role="group" aria-label="Evidence view"><button aria-pressed={view === 'disposition'} onClick={() => setView('disposition')}>Final disposition</button><button aria-pressed={view === 'agent'} disabled={!hasEvidence(workflow, agent)} onClick={() => setView('agent')}>Agent evidence</button></div>
          {view === 'agent' && hasEvidence(workflow, agent) ? <AgentInspector workflow={workflow} agent={agent} /> : <Disposition workflow={workflow} />}
        </> : <section className="panel pending-evidence"><SearchCheck size={35} strokeWidth={1.2} /><span className="eyebrow">EVIDENCE BEFORE CONCLUSIONS</span><h2>{run?.status === 'error' ? 'No result available' : 'Awaiting the investigation'}</h2><p>The reliability decision, engineering explanation, and agent findings will appear here when the API returns.</p><div><span>Observed measurements</span><ArrowRight size={14} /><span>Analytical evidence</span><ArrowRight size={14} /><span>Disposition</span></div></section>}
      </div>
    </div>
    {run?.status === 'success' && <details className="panel response-audit raw-output"><summary>Workflow audit · complete API response</summary><p>Original response, including fields not shown in the presentation. No analytical values are recalculated by this interface.</p><pre>{JSON.stringify(run.result.raw, null, 2)}</pre></details>}
  </div>;
}
