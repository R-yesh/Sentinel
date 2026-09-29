import { useCallback, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { DATASET_ID, sentinelApi } from '../api/client';
import { percent } from '../api/evaluation';
import { useResource } from '../hooks/useResource';
import { ErrorState, LoadingState } from '../components/States';
import { CoverageCharts } from '../features/evaluation/CoverageCharts';
import { EvaluationComparison } from '../features/evaluation/EvaluationComparison';
import { EvaluationTable } from '../features/evaluation/EvaluationTable';
import '../features/population/population.css';
import '../features/evaluation/evaluation.css';

export function EvaluationPage() {
  const load = useCallback((signal: AbortSignal) => sentinelApi.evaluation(DATASET_ID, signal), []);
  const resource = useResource(load);
  const [group, setGroup] = useState('not_flagged');
  const review = useRef<HTMLDivElement>(null);
  const data = resource.status === 'success' ? resource.data : null;
  return <div className="workspace-page evaluation-page">
    <div className="page-heading"><div><span className="eyebrow">EVALUATION / WHY SENTINEL?</span><h1>Why Sentinel<span className="heading-dot">?</span></h1><p>Synthetic retrospective evaluation</p></div><Link to="/overview" className="button secondary">Operational Overview</Link></div>
    <div className="evaluation-banner"><strong>EVALUATION MODE · HINDSIGHT VISIBLE</strong><p>Synthetic evaluation ground truth and future observations are visible here only for retrospective validation. They were not available to the operational 24h screening workflow.</p><span>Synthetic performance only · No real-world validation or detection guarantee · No Judge decisions</span></div>
    <section className="panel screening-perspectives" aria-label="Three levels of reliability evidence"><div><span className="eyebrow">01 / ABSOLUTE LEVEL</span><h2>Conventional reference</h2><p>Is observed 24h leakage above a fixed configured limit? This comparison uses one absolute measurement.</p><small>No industry-standard or synthetic acceptance limit is defined by this repository.</small></div><div><span className="eyebrow">02 / EARLY POPULATION SCREEN</span><h2>Sentinel screening</h2><p>Has leakage changed significantly since 0h, or is it unusually high relative to lot peers? Drift OR high-side robust lot evidence selects candidates.</p><small>Uses early observations only. No population-wide RF, Isolation Forest, or LLM execution.</small></div><div><span className="eyebrow">03 / INDIVIDUAL INVESTIGATION</span><h2>Follow the evidence</h2><p>On request, seven agents combine validation, model forecasts, uncertainty, multivariate Isolation Forest evidence, synthesis, challenge, and adjudication.</p><small>Only the Reliability Judge issues PASS / REVIEW / REJECT.</small><Link to="/dataset" className="text-button">Choose a component →</Link></div></section>
    {resource.status === 'loading' && <LoadingState label="Evaluating early screening against synthetic labels…" />}
    {resource.status === 'error' && <ErrorState message={resource.message} retry={resource.retry} />}
    {data && <>
      <div className="population-metrics" aria-label="Synthetic evaluation summary">{[
        ['Evaluated', data.summary.evaluated, `${data.summary.total} source rows · ${data.summary.excluded} excluded`],
        ['Synthetic defective', data.summary.defective.total, `${data.summary.healthy.total} synthetic healthy`],
        ['Early flagged', data.summary.candidates, `${percent(data.summary.screening_rate)} of evaluated components`],
        ['Defective flagged', data.summary.defective.flagged, `${percent(data.summary.defective.flag_rate)} of evaluated synthetic defects`],
        ['Healthy flagged', data.summary.healthy.flagged, `${percent(data.summary.healthy.flag_rate)} of evaluated healthy`],
        ['Defective not flagged', data.summary.defective.not_flagged, 'Openly inspect early-screening gaps below'],
      ].map(([label, count, note]) => <div className="panel population-metric" key={label}><span>{label}</span><strong>{count}</strong><small>{note}</small></div>)}</div>
      <CoverageCharts data={data} /><EvaluationComparison data={data} onSelect={(selection) => { setGroup(selection); review.current?.scrollIntoView?.({ block: 'start' }); }} /><div ref={review} className="evaluation-review-anchor"><EvaluationTable key={`${data.snapshot_id}/${group}`} data={data} filter={group} setFilter={setGroup} /></div>
      <details className="panel population-method"><summary>Evaluation definitions & limitations</summary><p>Source: {data.dataset_id} · Snapshot {data.snapshot_id} · Early screening method: {data.screening_method}. Healthy label: {data.healthy_label}. Synthetic defective labels: {data.defective_labels.join(', ')}.</p><p>Rates are percentages within evaluated rows, requiring a recognized synthetic label and a completed early screen. Excluded: {data.summary.excluded}; unknown labels: {data.summary.unknown_labels}. Missing future observations display as unavailable and do not affect screening or label-based rates.</p><p>Operational drift/lot candidate flags are joined with synthetic labels after screening. No RF/Isolation Forest population inference or Gemini calls are made. Future leakage is an observed synthetic outcome, not a model forecast or an operational input. This is descriptive evaluation on the existing synthetic dataset, not an independent held-out or real-world validation.</p></details>
    </>}
  </div>;
}
