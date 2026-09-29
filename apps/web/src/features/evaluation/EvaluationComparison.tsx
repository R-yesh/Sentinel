import type { EvaluationResponse } from '../../api/evaluation';

export function EvaluationComparison({ data }: { data: EvaluationResponse }) {
  const c = data.comparison;
  return <section className="panel screening-comparison" aria-label="Synthetic defective conventional comparison">
    <div className="population-panel-title"><span className="eyebrow">SYNTHETIC DEFECTIVE COMPONENTS ONLY</span><h2>Conventional vs Sentinel early screening</h2><p>Same early observations and Phase 4 rule; synthetic labels are used only to score retrospective coverage.</p></div>
    {c.status === 'unconfigured' ? <div className="comparison-unconfigured"><strong>Conventional comparison intentionally unavailable</strong><p>No authoritative conventional limit exists in this repository. Configure a domain-approved SENTINEL_CONVENTIONAL_24H_LIMIT_UA server-side to compare coverage. No threshold has been assumed.</p></div> : <>
      <div className="comparison-rule"><strong>Observed 24h leakage &gt; {c.limit_ua} µA</strong><span>Configured reference; domain approval is not established by this setting.</span></div>
      <div className="comparison-cells">{[['Conventional only', c.conventional_only], ['Both screens', c.both], ['Sentinel only', c.sentinel_only], ['Neither screen', c.neither]].map(([label, count]) => <div key={label}><span>{label}</span><strong>{count}</strong></div>)}</div>
      <p className="population-note">Synthetic defective flagged: conventional {c.conventional_flagged}, Sentinel {c.sentinel_flagged}. Comparable synthetic defective: {c.comparable_defective}; excluded: {c.excluded_defective}. “Sentinel only” means synthetic defective components flagged by Sentinel’s early screen but not by the configured conventional 24h rule.</p>
    </>}
  </section>;
}
