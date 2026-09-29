import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { ArrowDown, ArrowRight, ChevronLeft, ChevronRight, Database, FileSearch, RefreshCw, Search, SlidersHorizontal, X } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { DATASET_ID, sentinelApi } from '../../api/client';
import { useResource } from '../../hooks/useResource';
import { ErrorState, formatLeakage, LoadingState } from '../../components/States';
import { ComponentPreview, EmptyPreview } from './ComponentPreview';

function positivePage(value: string | null) {
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : 1;
}

export function DatasetPage() {
  const [params, setParams] = useSearchParams();
  const search = params.get('search') || '';
  const page = positivePage(params.get('page'));
  const pageSize = [10, 25, 50, 100].includes(Number(params.get('pageSize'))) ? Number(params.get('pageSize')) : 25;
  const selected = params.get('component');
  const [draft, setDraft] = useState(search);
  useEffect(() => { setDraft(search); }, [search]);
  const load = useCallback((signal: AbortSignal) => sentinelApi.components(DATASET_ID, search, page, pageSize, signal), [search, page, pageSize]);
  const result = useResource(load);
  // A separate unfiltered request gives a truthful dataset count while searching.
  const summaryLoad = useCallback((signal: AbortSignal) => sentinelApi.components(DATASET_ID, '', 1, 1, signal), []);
  const summary = useResource(summaryLoad);
  const update = (changes: Record<string, string | null>, replace = false) => {
    setParams((current) => {
      const next = new URLSearchParams(current);
      for (const [key, value] of Object.entries(changes)) value === null ? next.delete(key) : next.set(key, value);
      return next;
    }, { replace });
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const query = draft.trim();
    if (query === search && page === 1) result.retry();
    else update({ search: query || null, page: null, component: null });
  };
  const clearSearch = () => { setDraft(''); update({ search: null, page: null, component: null }); };
  const total = result.status === 'success' ? result.data.total : null;
  const pages = total === null ? null : Math.max(1, Math.ceil(total / pageSize));
  const refresh = () => { result.retry(); summary.retry(); };

  return <div className="workspace-page">
    <div className="page-heading"><div><div className="eyebrow">BURN-IN INTELLIGENCE <span>/</span> DATA EXPLORER</div><h1>Dataset workspace<span className="heading-dot">.</span></h1><p>Inspect early observations. Select a component. Follow the evidence.</p></div><span className="outline-badge"><span className="status-dot" />SYNTHETIC DATASET</span></div>
    <section className="dataset-summary panel" aria-label="Dataset summary">
      <div className="dataset-identity"><span className="dataset-icon"><Database size={23} strokeWidth={1.5} /></span><div><span className="tiny-label">ACTIVE DATASET</span><h2>{summary.status === 'success' ? summary.data.dataset_id : DATASET_ID}</h2><p>Semiconductor burn-in · demonstration data</p></div></div>
      <div className="summary-stat"><span className="tiny-label">TOTAL COMPONENTS</span><strong>{summary.status === 'success' ? summary.data.total.toLocaleString() : '—'}</strong><span>{summary.status === 'error' ? 'Count unavailable' : summary.status === 'loading' ? 'Loading count…' : 'From source dataset'}</span></div>
      <div className="summary-stat"><span className="tiny-label">OBSERVED WINDOW</span><strong>0h <span className="stat-arrow">→</span> 24h</strong><span>Leakage current · µA</span></div>
      <div className="summary-tag"><span className="tiny-label">DATA PROVENANCE</span><span className="neutral-tag">Observed inputs</span><span>No forecasts in this view</span></div>
    </section>

    <div className="workspace-grid">
      <section className="component-browser panel" aria-labelledby="components-heading">
        <div className="table-title"><div><h2 id="components-heading">Components</h2><span>{total === null ? 'Reading dataset' : `${total.toLocaleString()} ${search ? 'matching' : 'available'} ${total === 1 ? 'component' : 'components'}`}</span></div><button className="icon-button" title="Refresh dataset" aria-label="Refresh dataset" onClick={refresh} disabled={result.status === 'loading'}><RefreshCw size={16} /></button></div>
        <div className="table-toolbar"><form className="search-form" onSubmit={submit} role="search"><Search size={17} /><input aria-label="Search component or lot ID" placeholder="Search component or lot ID…" value={draft} onChange={(event) => setDraft(event.target.value)} />{draft && <button type="button" className="icon-button clear-search" onClick={clearSearch} aria-label="Clear search"><X size={14} /></button>}<button type="submit" className="search-submit">Search</button></form><span className="table-source"><SlidersHorizontal size={14} />0h / 24h</span></div>
        {search && <div className="active-search">Results for <strong>“{search}”</strong><button onClick={clearSearch}>Clear filter <X size={12} /></button></div>}
        <div className="table-container" aria-busy={result.status === 'loading'}>
          {result.status === 'loading' && <LoadingState label="Loading observed measurements…" />}
          {result.status === 'error' && <ErrorState message={result.message} retry={result.retry} />}
          {result.status === 'success' && (result.data.items.length ? <table>
            <caption className="sr-only">Observed component leakage in microamperes. Select a component to inspect its measurements.</caption>
            <thead><tr><th scope="col">Component ID <ArrowDown size={12} aria-label="Sorted ascending" /></th><th scope="col">Lot ID</th><th scope="col" className="numeric">Leakage 0h <span>µA</span></th><th scope="col" className="numeric">Leakage 24h <span>µA</span></th><th scope="col"><span className="sr-only">Selection</span></th></tr></thead>
            <tbody>{result.data.items.map((item) => <tr key={item.component_id} className={selected === item.component_id ? 'selected' : ''} onClick={() => update({ component: item.component_id }, true)}>
              <td><button className="component-link" aria-pressed={selected === item.component_id} onClick={(event) => { event.stopPropagation(); update({ component: item.component_id }, true); }}><span className="row-chip" />{item.component_id}</button></td>
              <td><span className="lot-cell">{item.lot_id}</span></td><td className="numeric">{formatLeakage(item.leakage_0h)}</td><td className="numeric">{formatLeakage(item.leakage_24h)}</td><td className="row-arrow"><ArrowRight size={14} /></td>
            </tr>)}</tbody>
          </table> : <div className="state-message"><FileSearch size={30} strokeWidth={1.4} /><h3>{search ? 'No matching components' : page > 1 ? 'No components on this page' : 'No components available'}</h3><p>{search ? `No component or lot ID matches “${search}”.` : 'Try returning to the first page or refreshing the dataset.'}</p><button className="button secondary" onClick={() => { clearSearch(); if (page === 1 && !search) refresh(); }}>{search ? 'Clear search' : 'Return to dataset'}</button></div>)}
        </div>
        <div className="pagination"><span role="status">{result.status === 'success' ? result.data.items.length ? `${((page - 1) * pageSize + 1).toLocaleString()}–${((page - 1) * pageSize + result.data.items.length).toLocaleString()} of ${result.data.total.toLocaleString()}` : '0 shown' : '—'}</span><div><label>Rows <select aria-label="Rows per page" value={pageSize} onChange={(event) => update({ pageSize: event.target.value, page: null, component: null })}>{[10, 25, 50, 100].map((size) => <option key={size} value={size}>{size}</option>)}</select></label><span className="page-count">{pages === null ? '—' : `Page ${page} / ${pages}`}</span><button className="icon-button" aria-label="Previous page" disabled={page <= 1 || result.status === 'loading'} onClick={() => update({ page: String(page - 1), component: null })}><ChevronLeft size={17} /></button><button className="icon-button" aria-label="Next page" disabled={pages === null || page >= pages || result.status === 'loading'} onClick={() => update({ page: String(page + 1), component: null })}><ChevronRight size={17} /></button></div></div>
      </section>
      {selected ? <ComponentPreview key={selected} datasetId={DATASET_ID} componentId={selected} onClose={() => update({ component: null }, true)} /> : <EmptyPreview />}
    </div>
    <div className="workspace-footnote"><span className="status-dot" /><p><strong>Observation integrity</strong> · Values are displayed to four decimal places. Source precision is retained by the backend.</p></div>
  </div>;
}
