import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { PopulationResponse } from '../../api/population';
import { useInvestigationSession } from '../investigation/InvestigationSession';

const display = (value: number | null, digits = 4) => value === null ? 'Unavailable' : value.toFixed(digits);
export function ScreeningTable({ data, lot, setLot }: { data: PopulationResponse; lot: string; setLot: (value: string) => void }) {
  const [filter, setFilter] = useState('candidates');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  useEffect(() => { setPage(1); }, [lot]);
  const navigate = useNavigate();
  const { start } = useInvestigationSession();
  const matches = data.components.filter((row) => (!lot || row.lot_id === lot) && row.component_id.toLowerCase().includes(search.toLowerCase().trim()) && (
    filter === 'all' || filter === 'candidates' && row.candidate === true || filter === 'unassessed' && row.candidate === null ||
    filter === 'sentinel_only' && row.candidate === true && row.conventional_flag === false || row.reasons.includes(filter)
  ));
  const current = Math.min(page, Math.max(1, Math.ceil(matches.length / 15)));
  return <section className="panel screening-table" aria-label="Population screening components">
    <div className="population-panel-title"><span className="eyebrow">INVESTIGATION QUEUE / SCREENING EVIDENCE</span><h2>Components to inspect</h2><p>Ordered by number of screening reasons, then component ID. This is not a reliability-risk ranking.</p></div>
    <div className="screening-filters"><input aria-label="Search population component" placeholder="Find component…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} /><select aria-label="Screening evidence filter" value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1); }}>
      <option value="candidates">Screening candidates</option><option value="significant_early_drift">Significant early drift</option><option value="high_side_lot_deviation">High-side lot evidence</option><option value="sentinel_only" disabled={data.comparison.status !== 'configured'}>Sentinel only</option><option value="unassessed">Unassessed / data issues</option><option value="all">All components</option>
    </select><select aria-label="Manufacturing lot filter" value={lot} onChange={(e) => { setLot(e.target.value); setPage(1); }}><option value="">All lots</option>{data.lots.map((item) => <option key={item.lot_id}>{item.lot_id}</option>)}</select><span>{matches.length} matching components</span></div>
    <div className="population-table-scroll"><table><caption className="sr-only">Observed measurements and derived screening evidence. No final reliability decisions.</caption><thead><tr><th>Component / lot</th><th>Observed 0h<br /><small>µA</small></th><th>Observed 24h<br /><small>µA</small></th><th>Derived change<br /><small>%</small></th><th>Lot evidence</th><th>Screening reasons</th><th>Action</th></tr></thead><tbody>{matches.slice((current - 1) * 15, current * 15).map((row) => <tr key={row.component_id}>
      <td><strong>{row.component_id}</strong><small>{row.lot_id}</small></td><td>{display(row.leakage_0h)}</td><td>{display(row.leakage_24h)}</td><td>{display(row.percentage_change, 2)}</td><td>{row.lot_evidence?.replaceAll('_', ' ') ?? 'Unavailable'}<small>z: {typeof row.robust_z_score === 'number' ? row.robust_z_score.toFixed(2) : row.robust_z_score ?? '—'}</small></td><td>{row.issue ?? (row.reasons.length ? row.reasons.map((reason) => <span className="screening-reason" key={reason}>{reason === 'significant_early_drift' ? 'Significant early drift' : 'High-side lot deviation'}</span>) : 'No screening signal')}</td><td><button className="button secondary" aria-label={`Investigate ${row.component_id}`} onClick={() => { start({ dataset_id: data.dataset_id, component_id: row.component_id }, row); navigate(`/analysis?${new URLSearchParams({ dataset: data.dataset_id, component: row.component_id })}`); }}>Investigate</button></td>
    </tr>)}</tbody></table></div>
    {!matches.length && <p className="population-empty">No components match these filters.</p>}
    <div className="screening-pagination"><span>Page {current} / {Math.max(1, Math.ceil(matches.length / 15))} · 15 rows per page</span><button className="button secondary" disabled={current <= 1} onClick={() => setPage(current - 1)}>Previous</button><button className="button secondary" disabled={current * 15 >= matches.length} onClick={() => setPage(current + 1)}>Next</button></div>
  </section>;
}
