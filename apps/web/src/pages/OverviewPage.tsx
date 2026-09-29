import { useCallback, useState } from 'react';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { DATASET_ID, sentinelApi } from '../api/client';
import { useResource } from '../hooks/useResource';
import { ErrorState, LoadingState } from '../components/States';
import { DriftDistribution, LotDistribution } from '../features/population/PopulationCharts';
import { ScreeningComparison } from '../features/population/ScreeningComparison';
import { ScreeningTable } from '../features/population/ScreeningTable';
import '../features/population/population.css';

export function OverviewPage() {
  const load = useCallback((signal: AbortSignal) => sentinelApi.population(DATASET_ID, signal), []);
  const resource = useResource(load);
  const [lot, setLot] = useState('');
  const data = resource.status === 'success' ? resource.data : null;
  return <div className="workspace-page command-center">
    <div className="page-heading"><div><span className="eyebrow">SENTINEL / POPULATION AWARENESS</span><h1>Reliability command center<span className="heading-dot">.</span></h1><p>Screen the population. Locate the evidence. Investigate the component.</p></div><Link className="button secondary" to="/dataset">Dataset workspace<ArrowRight size={15} /></Link></div>
    <div className="population-source"><div><span className="neutral-tag">SYNTHETIC BURN-IN DATASET</span><code>{DATASET_ID}</code><span>Observed window: 0h → 24h</span></div><button className="icon-button" aria-label="Refresh population" disabled={resource.status === 'loading'} onClick={resource.retry}><RefreshCw size={16} /></button></div>
    {resource.status === 'loading' && <LoadingState label="Screening observed population… No LLM investigation is being run." />}
    {resource.status === 'error' && <ErrorState message={resource.message} retry={resource.retry} />}
    {data && <>
      <div className="population-metrics" aria-label="Population summary">{[
        ['Components', data.summary.total, `${data.summary.lots} manufacturing lots`],
        ['Screening candidates', data.summary.candidates, 'Drift or high-side lot evidence'],
        ['Significant early drift', data.summary.significant_drift, `Observed change ≥ ${data.early_drift_threshold_percent}%`],
        ['High-side lot evidence', data.summary.high_side_lot, 'Elevated, strong, or outlier'],
        ['No screening signal', data.summary.no_screening_signal, 'Not a judge-issued PASS'],
        ['Unassessed', data.summary.unassessed, 'Input or peer context issues'],
      ].map(([label, count, note]) => <div className="panel population-metric" key={label}><span>{label}</span><strong>{typeof count === 'number' ? count.toLocaleString() : count}</strong><small>{note}</small></div>)}</div>
      <p className="screening-boundary">Screening identifies candidates for investigation. It does not issue PASS, REVIEW, or REJECT. Signal counts overlap; candidate count is their union.</p>
      <div className="population-charts"><DriftDistribution data={data} /><LotDistribution lots={data.lots} selected={lot} onSelect={setLot} /></div>
      <ScreeningComparison data={data} />
      <ScreeningTable key={data.snapshot_id} data={data} lot={lot} setLot={setLot} />
      <details className="panel population-method"><summary>Screening method & provenance</summary><p>A candidate has early leakage change ≥ {data.early_drift_threshold_percent}% OR HIGH-direction, non-TYPICAL evidence from Sentinel’s existing robust lot detector. Each component is excluded from its own paired lot peers. Missing/invalid measurements or peer context remain unassessed.</p><p>Percentage change and slope use the existing early-feature utility, including its 0% change convention for a zero baseline. This is not an assertion of no absolute change. No synthetic defect labels or future observations are used.</p><p>Isolation Forest, RF forecasts, tree disagreement, adversarial review, and final decisions remain in individual investigations. They are not computed or counted by this population screen. No LLM calls run on dashboard load.</p><p>Snapshot {data.snapshot_id} · Method {data.method} · {data.summary.screened} fully screened. In-memory analysis is cached by observed snapshot and conventional configuration. Refresh rereads the dataset.</p></details>
    </>}
  </div>;
}
