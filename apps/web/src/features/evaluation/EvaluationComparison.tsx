import type { EvaluationResponse } from '../../api/evaluation';

export function EvaluationComparison({ data, onSelect }: { data: EvaluationResponse; onSelect?: (group: string) => void }) {
  const c = data.comparison;
  return <section className="panel screening-comparison" aria-label="Synthetic defective conventional comparison">
    <div className="population-panel-title"><span className="eyebrow">SYNTHETIC DEFECTIVE COMPONENTS ONLY</span><h2>Conventional vs Sentinel early screening</h2><p>Same early observations; synthetic labels are used only to evaluate retrospective coverage.</p></div>
    {c.status === 'unconfigured' ? <div className="comparison-unconfigured"><strong>Conventional comparison intentionally unavailable</strong><p>No authoritative conventional limit exists in this repository. Configure a domain-approved SENTINEL_CONVENTIONAL_24H_LIMIT_UA server-side to compare coverage. No threshold has been assumed.</p></div> : <>
      <div className="comparison-rule"><strong>Observed 24h leakage &gt; {c.limit_ua} µA</strong><span>Configured reference; domain approval is not established by this setting.</span></div>
      <div className="comparison-cells comparison-actions">{([['Sentinel only', 'sentinel_only', c.sentinel_only], ['Conventional only', 'conventional_only', c.conventional_only], ['Both', 'both', c.both], ['Neither', 'neither', c.neither]] as const).map(([label, group, count]) => <button key={group} onClick={() => onSelect?.(group)} disabled={!onSelect} aria-label={`Inspect ${label.toLowerCase()} synthetic defects`}><span>{label}</span><strong>{count}</strong><small>{c.comparable_defective ? `${((count ?? 0) / c.comparable_defective * 100).toFixed(1)}% of comparable defects` : 'No comparable defects'}</small><span className="comparison-inspect">Inspect components →</span></button>)}</div>
      <p className="population-note">Synthetic defective flagged: conventional {c.conventional_flagged}, Sentinel {c.sentinel_flagged}. Comparable synthetic defective: {c.comparable_defective}; excluded: {c.excluded_defective}. “Sentinel only” means synthetic defective components flagged by Sentinel’s early screen but not by the configured conventional 24h rule.</p>
    </>}
  </section>;
}
