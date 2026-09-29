import { ShieldCheck, ShieldAlert, ShieldX, CircleHelp } from 'lucide-react';
import { text, type WorkflowState } from '../../api/investigation';
import { contributedAgents, humanize } from './presentation';
import { EvidenceList, Narrative } from './Evidence';

export function Disposition({ workflow }: { workflow: WorkflowState }) {
  const decision = workflow.final_decision;
  const judge = workflow.agent_outputs.reliability_judge ?? {};
  const explanation = workflow.agent_outputs.explanation ?? {};
  const Icon = decision === 'PASS' ? ShieldCheck : decision === 'REVIEW' ? ShieldAlert : decision === 'REJECT' ? ShieldX : CircleHelp;
  const validationStopped = workflow.agent_outputs.data_forensics?.passed === false && !decision;
  return <section className={`panel disposition disposition-${decision?.toLowerCase() ?? 'none'}`} aria-label="Reliability disposition">
    <div className="disposition-heading"><div><span className="tiny-label">RELIABILITY DISPOSITION</span><h2><Icon size={30} strokeWidth={1.5} />{decision ?? 'No decision issued'}</h2></div><span className="workflow-status">{humanize(workflow.status)}</span></div>
    <div className="disposition-body">
      <div className="disposition-identity"><span>{workflow.component_id}</span><span>{workflow.lot_id ?? 'Lot not provided'}</span></div>
      {!decision && <p className="provenance-note">{validationStopped ? 'Data Forensics stopped the workflow. Review the validation evidence; this is not a judge-issued REVIEW decision.' : 'The response contains no recognized final decision. Inspect the available evidence and response notes.'}</p>}
      {text(explanation.headline) && <h3 className="disposition-headline">{text(explanation.headline)}</h3>}
      <p className="decision-reason-code">{text(judge.reason_code) ?? 'Reason code not provided'}</p>
      <Narrative title="Engineering explanation" value={workflow.explanation ?? explanation.decision_reasoning} />
      {text(explanation.summary) && <Narrative title="Summary" value={explanation.summary} />}
      <details><summary>Judge reasoning</summary><Narrative title="Decision rationale" value={judge.reasoning} /></details>
      <EvidenceList title="Supporting evidence" value={judge.supporting_evidence} />
      <EvidenceList title="Unresolved concerns" value={judge.unresolved_concerns} />
      <div className="recommended-action"><Narrative title="Recommended action" value={explanation.recommended_action} /></div>
      <div className="decision-audit"><span>{contributedAgents(workflow).length} agents with returned evidence</span><span>{workflow.findings.length} recorded findings</span></div>
    </div>
  </section>;
}
