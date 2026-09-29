import type { LotSummary, PopulationResponse } from '../../api/population';

export function DriftDistribution({ data }: { data: PopulationResponse }) {
  const max = Math.max(1, ...data.drift_histogram.map((bin) => bin.count));
  return <section className="panel population-chart" aria-label="Early drift distribution">
    <div className="population-panel-title"><span className="eyebrow">DERIVED / OBSERVED CHANGE</span><h2>Early drift distribution</h2><p>0h → 24h change · % · {data.summary.screened} fully screened components</p></div>
    {data.drift_histogram.length ? <div className="histogram">{data.drift_histogram.map((bin, i) => <div className="histogram-column" key={i}>
      <div className="histogram-track"><div className="histogram-bar" style={{ height: `${bin.count / max * 100}%` }} tabIndex={0} aria-label={`${bin.lower.toFixed(2)} to ${bin.upper.toFixed(2)} percent: ${bin.count} components`}><span className="chart-tooltip">{bin.count} components · {bin.lower.toFixed(2)}–{bin.upper.toFixed(2)}%</span><span className="bar-count">{bin.count}</span></div></div>
      <span className="bin-label">{bin.lower.toFixed(1)}<br />{bin.upper.toFixed(1)}</span>
    </div>)}</div> : <p className="population-note">No fully screened observations available.</p>}
    <p className="population-note">Bar height = component count. Labels show each bin’s lower/upper bound (%). Final bin includes its upper bound. Drift screening activates at ≥ {data.early_drift_threshold_percent}%.</p>
  </section>;
}

export function LotDistribution({ lots, selected, onSelect }: { lots: LotSummary[]; selected: string; onSelect: (lot: string) => void }) {
  return <section className="panel population-chart" aria-label="Lot screening context">
    <div className="population-panel-title"><span className="eyebrow">MANUFACTURING LOT CONTEXT</span><h2>Candidates within each lot</h2><p>Candidate / total components · select a lot to filter the table</p></div>
    <div className="lot-bars">{lots.map((lot) => <button key={lot.lot_id} className={`lot-bar-row ${selected === lot.lot_id ? 'selected' : ''}`} aria-pressed={selected === lot.lot_id} onClick={() => onSelect(selected === lot.lot_id ? '' : lot.lot_id)} title={`${lot.screened} screened; ${lot.unassessed} unassessed`}>
      <span>{lot.lot_id}</span><span className="lot-bar-track"><span style={{ width: `${lot.total ? lot.candidates / lot.total * 100 : 0}%` }} /></span><strong>{lot.candidates}<small> / {lot.total}</small></strong>
    </button>)}</div>
    <p className="population-note">Cyan = screening candidates; track = full lot population. Unusual components do not establish a lot-wide manufacturing defect.</p>
  </section>;
}
