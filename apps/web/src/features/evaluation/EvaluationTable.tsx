import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { EvaluationResponse } from '../../api/evaluation';
import { useInvestigationSession } from '../investigation/InvestigationSession';

const value = (n: number | null) => n === null ? 'Unavailable' : n.toFixed(4);
export function EvaluationTable({ data }: { data: EvaluationResponse }) {
  const [filter, setFilter] = useState('not_flagged');
  const [type, setType] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const { start } = useInvestigationSession(); const navigate = useNavigate();
  const rows = data.components.filter((r) => (!type || (r.hindsight.defect_type ?? '(missing)') === type) && r.early.component_id.toLowerCase().includes(search.toLowerCase().trim()) && (
    filter === 'all' || filter === 'excluded' && !r.evaluated || r.hindsight.synthetic_class === 'defective' && r.evaluated && (filter === 'not_flagged' ? r.early.candidate === false : r.comparison_bucket === filter)
  ));
  return <section className="panel screening-table evaluation-table" aria-label="Retrospective component review">
    <div className="population-panel-title"><span className="eyebrow">MISS ANALYSIS / SYNTHETIC EVALUATION</span><h2>What the early screen did not flag</h2><p>Unflagged synthetic defects are shown by default. Future observations used only for retrospective evaluation.</p></div>
    <div className="screening-filters"><input aria-label="Search evaluation component" placeholder="Find component…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} /><select aria-label="Evaluation group" value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1); }}><option value="not_flagged">Synthetic defective · not flagged</option>{['sentinel_only', 'conventional_only', 'both', 'neither'].map((group) => <option key={group} value={group} disabled={data.comparison.status !== 'configured'}>Synthetic defective · {group.replaceAll('_', ' ')}</option>)}<option value="excluded">Excluded from evaluation</option><option value="all">All synthetic components</option></select><select aria-label="Synthetic defect type" value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}><option value="">All types</option>{data.by_defect_type.map((item) => <option key={item.defect_type}>{item.defect_type}</option>)}</select><span>{rows.length} components</span></div>
    <div className="population-table-scroll"><table><caption className="sr-only">Early observations separated from synthetic evaluation ground truth and future observations.</caption><thead><tr className="evaluation-column-groups"><th colSpan={4}>Available early / operational observations</th><th colSpan={3}>Evaluation-only / hindsight</th><th colSpan={2}>Early screen / investigate</th></tr><tr><th>Component</th><th>Lot</th><th>0h · µA</th><th>24h · µA</th><th>Synthetic defect type</th><th>96h · µA<br />Future observation</th><th>168h · µA<br />Future observation</th><th>Early signals</th><th>Action</th></tr></thead><tbody>{rows.slice((page - 1) * 12, page * 12).map((row) => <tr key={row.early.component_id}><td>{row.early.component_id}</td><td>{row.early.lot_id}</td><td>{value(row.early.leakage_0h)}</td><td>{value(row.early.leakage_24h)}</td><td className="hindsight-cell">{row.hindsight.defect_type ?? 'Unknown'}</td><td className="hindsight-cell">{value(row.hindsight.leakage_96h)}</td><td className="hindsight-cell">{value(row.hindsight.leakage_168h)}</td><td>{row.early.candidate === null ? 'Unassessed' : row.early.reasons.length ? row.early.reasons.map((r) => <span className="screening-reason" key={r}>{r === 'significant_early_drift' ? 'Drift' : 'High-side lot'}</span>) : 'Neither'}</td><td><button className="button secondary" aria-label={`Investigate ${row.early.component_id}`} onClick={() => {
      const { component_id, lot_id, leakage_0h, leakage_24h } = row.early;
      start({ dataset_id: data.dataset_id, component_id }, { component_id, lot_id, leakage_0h, leakage_24h });
      navigate(`/analysis?${new URLSearchParams({ dataset: data.dataset_id, component: component_id })}`);
    }}>Investigate</button></td></tr>)}</tbody></table></div>
    {!rows.length && <p className="population-empty">No components in this evaluation group.</p>}
    <div className="screening-pagination"><span>Page {page} / {Math.max(1, Math.ceil(rows.length / 12))}</span><button className="button secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><button className="button secondary" disabled={page * 12 >= rows.length} onClick={() => setPage(page + 1)}>Next</button></div><p className="population-note">Investigate starts the unchanged Phase 3 workflow using dataset/component identity and legitimate early inputs. Synthetic labels and future observations are not sent to the investigation.</p>
  </section>;
}
