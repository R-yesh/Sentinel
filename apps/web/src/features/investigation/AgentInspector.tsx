import { Crosshair } from 'lucide-react';
import { duration, type AgentExecution } from '../../api/execution';
import { isRecord, text, type AgentId, type WorkflowState } from '../../api/investigation';
import { AGENTS, humanize, measurement, METRICS } from './presentation';
import { EvidenceList, FieldValue, Narrative } from './Evidence';

export function AgentInspector({ workflow, agent, execution }: { workflow: WorkflowState; agent: AgentId; execution?: AgentExecution }) {
  const output = workflow.agent_outputs[agent] ?? {};
  const findings = workflow.findings.filter((finding) => finding.agent === agent);
  const metrics = METRICS[agent] ?? [];
  const review = isRecord(output.review) ? output.review : {};
  const specialized = new Set([
    ...metrics.map((metric) => metric.key),
    ...(agent === 'adversarial_qa' ? ['review'] : []),
    ...(agent === 'reliability_judge' ? ['reasoning', 'supporting_evidence', 'unresolved_concerns'] : []),
    ...(agent === 'explanation' ? ['summary', 'key_evidence', 'adversarial_context', 'decision_reasoning', 'recommended_action'] : []),
  ]);
  const remaining = Object.fromEntries(Object.entries(output).filter(([key]) => !specialized.has(key)));
  return <section className="panel agent-inspector" aria-label="Agent details">
    <div className="panel-heading"><span><Crosshair size={16} /> EVIDENCE INSPECTOR</span><span className="tiny-label">API RESULT</span></div>
    <div className="inspector-body">
      <span className="eyebrow">{AGENTS[agent].kind}</span><h2>{AGENTS[agent].name}</h2>
      <p className="inspector-description">{AGENTS[agent].description}</p>
      <div className="inspector-execution"><strong>Execution: {execution?.status.replaceAll('_', ' ') ?? 'timing unavailable'}</strong><span>{duration(execution?.duration_ms)}</span>{execution?.started_at && <details><summary>Execution timestamps · UTC</summary><p>Started: {execution.started_at}<br />Finished: {execution.completed_at}</p><p>Workflow offsets: {duration(execution.start_offset_ms)} → {duration(execution.end_offset_ms)}</p></details>}</div>
      {metrics.length > 0 && <dl className="agent-metrics">{metrics.map((metric) => {
        let value = output[metric.key];
        if (metric.percentile && typeof value === 'number') value *= 100;
        return <div key={metric.key}><dt>{metric.label}</dt><dd>{measurement(value, metric.digits ?? 4)}{value != null && <small>{metric.unit}</small>}</dd></div>;
      })}</dl>}
      {agent === 'drift_intelligence' && <p className="provenance-note">0h/24h change and slope derive from observations. The 168h value is a forecast; tree disagreement is not a calibrated confidence interval.</p>}
      {agent === 'lot_intelligence' && <p className="provenance-note">Robust statistics describe observed lot-relative deviation. Isolation Forest is model-derived anomaly evidence. Neither score is a probability of failure.</p>}
      {Object.keys(remaining).length > 0 && <section className="evidence-section"><h3>{agent === 'data_forensics' ? 'Component & lot validation' : 'Structured assessment'}</h3><FieldValue value={remaining} /></section>}
      {agent === 'adversarial_qa' && <>
        <Narrative title="Challenged assessment" value={review.challenged_assessment} />
        <Narrative title="Unresolved conflict" value={review.unresolved_conflict} />
        <section className="evidence-section"><h3>Adversarial challenges</h3>{Array.isArray(review.challenges) && review.challenges.length ? review.challenges.map((challenge, index) => isRecord(challenge)
          ? <article className="challenge-card" key={index}><div><span className="neutral-tag">{text(challenge.direction) ?? 'Direction unavailable'}</span><small>{text(challenge.challenge_type) ? humanize(challenge.challenge_type as string) : 'Type unavailable'}</small></div><p>{text(challenge.summary) ?? 'Summary unavailable.'}</p></article>
          : <p key={index} className="not-provided">Unreadable challenge; see raw output.</p>) : <p className="not-provided">{Array.isArray(review.challenges) ? 'None reported.' : 'Review not provided.'}</p>}</section>
      </>}
      {agent === 'reliability_judge' && <><Narrative title="Judge reasoning" value={output.reasoning} /><EvidenceList title="Supporting evidence" value={output.supporting_evidence} /><EvidenceList title="Unresolved concerns" value={output.unresolved_concerns} /></>}
      {agent === 'explanation' && <><Narrative title="Engineering summary" value={output.summary} /><EvidenceList title="Key evidence" value={output.key_evidence} /><EvidenceList title="Adversarial context" value={output.adversarial_context} /><Narrative title="Decision reasoning" value={output.decision_reasoning} /><Narrative title="Recommended action" value={output.recommended_action} /></>}
      <section className="evidence-section"><h3>Recorded findings <span className="count-tag">{findings.length}</span></h3>{findings.length === 0 && <p className="not-provided">No finding returned for this agent.</p>}{findings.map((finding, index) => <article className="finding-card" key={index}>
        <div className="finding-tags"><span className={`severity severity-${finding.severity}`}>{finding.severity ?? 'Severity unavailable'}</span><code>{finding.finding_type}</code></div>
        <p>{finding.summary}</p><EvidenceList title="Evidence" value={finding.evidence} />
        <details><summary>Finding metadata</summary><FieldValue value={finding.metadata} /></details>
      </article>)}</section>
      <details className="raw-output"><summary>Raw output · {AGENTS[agent].name}</summary><pre>{JSON.stringify({ output: workflow.agent_outputs[agent] ?? null, findings }, null, 2)}</pre></details>
    </div>
  </section>;
}
