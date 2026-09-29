import type { PopulationResponse } from '../../api/population';

export function ScreeningComparison({ data }: { data: PopulationResponse }) {
  const c = data.comparison;
  const cells = [
    ['Conventional only', c.conventional_only], ['Both methods', c.both],
    ['Sentinel only', c.sentinel_only], ['Neither method', c.neither],
  ] as const;
  return <section className="panel screening-comparison" aria-label="Conventional versus Sentinel screening">
    <div className="population-panel-title"><span className="eyebrow">SCREENING COVERAGE / NOT JUDGE DECISIONS</span><h2>Conventional vs Sentinel</h2><p>Compare a simple absolute 24h leakage limit with drift and lot-relative evidence.</p></div>
    {c.status === 'unconfigured' ? <div className="comparison-unconfigured"><strong>Conventional reference not configured</strong><p>No authoritative conventional limit is defined in this repository. A domain-approved value is required before overlap counts can be reported.</p><span>Comparison rule: observed 24h leakage &gt; configured limit (µA).</span></div>
      : <><div className="comparison-rule"><strong>Configured reference: 24h leakage &gt; {c.limit_ua} µA</strong><span>Explicit comparison setting; domain approval is not established by this dashboard.</span></div><div className="comparison-cells">{cells.map(([label, count]) => <div key={label}><span>{label}</span><strong>{count?.toLocaleString() ?? '—'}</strong></div>)}</div><p className="population-note">Conventional flags: {(c.conventional_only! + c.both!).toLocaleString()} · Sentinel candidates: {(c.sentinel_only! + c.both!).toLocaleString()} · Comparable: {c.comparable} · Excluded: {c.excluded}. Groups are mutually exclusive. “Sentinel only” means not flagged by this configured rule, not a confirmed missed defect.</p></>}
  </section>;
}
