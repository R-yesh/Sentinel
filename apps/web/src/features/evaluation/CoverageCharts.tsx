import { percent, type EvaluationResponse } from '../../api/evaluation';

export function CoverageCharts({ data }: { data: EvaluationResponse }) {
  const buckets = [['Drift only', data.signal_overlap.drift_only], ['Lot only', data.signal_overlap.lot_only], ['Both signals', data.signal_overlap.both], ['Neither signal', data.signal_overlap.neither]] as const;
  return <div className="evaluation-charts">
    <section className="panel" aria-label="Screening coverage by synthetic defect type">
      <div className="population-panel-title"><span className="eyebrow">SYNTHETIC EVALUATION GROUND TRUTH</span><h2>Which classes were flagged early?</h2><p>Flag rate = early candidates / evaluated components in each class.</p></div>
      <div className="evaluation-coverage"><table><thead><tr><th>Synthetic class</th><th>Total</th><th>Flagged</th><th>Not flagged</th><th>Excluded</th><th>Flag rate</th></tr></thead><tbody>{data.by_defect_type.map((group) => <tr key={group.defect_type}><th scope="row">{group.defect_type}<span className="coverage-track" aria-hidden="true"><span style={{ width: `${group.flag_rate ?? 0}%` }} /></span></th><td>{group.total}</td><td>{group.flagged}</td><td>{group.not_flagged}</td><td>{group.excluded}</td><td>{percent(group.flag_rate)}</td></tr>)}</tbody></table></div>
      <p className="population-note">Bars use a shared 0–100% scale. Flagging a healthy synthetic component is a screening false alarm, not a Judge rejection. Unknown labels and incomplete early screening are excluded from rates.</p>
    </section>
    <section className="panel" aria-label="Early signal overlap"><div className="population-panel-title"><span className="eyebrow">EARLY EVIDENCE / RETROSPECTIVE COUNTS</span><h2>How the signals contributed</h2><p>Mutually exclusive groups across {data.summary.evaluated} evaluated components.</p></div>
      <div className="overlap-list">{buckets.map(([label, count]) => <div key={label}><span>{label}</span><strong>{count}</strong><small>{percent(data.summary.evaluated ? count / data.summary.evaluated * 100 : null)}</small></div>)}</div>
      <p className="population-note">Drift only + lot only + both = early Sentinel candidates. Neither = evaluated components without an early screening signal. These are not final reliability dispositions.</p>
    </section>
  </div>;
}
