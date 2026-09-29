import { useCallback, useEffect, useRef } from 'react';
import { ArrowRight, Box, Check, Crosshair, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { sentinelApi } from '../../api/client';
import { useResource } from '../../hooks/useResource';
import { ErrorState, formatLeakage, LoadingState } from '../../components/States';

export function ComponentPreview({ datasetId, componentId, onClose }: {
  datasetId: string; componentId: string; onClose: () => void;
}) {
  const load = useCallback((signal: AbortSignal) => sentinelApi.component(datasetId, componentId, signal), [datasetId, componentId]);
  const result = useResource(load);
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    if (result.status === 'success' && window.matchMedia?.('(max-width: 1050px)').matches) {
      panel.current?.scrollIntoView({ block: 'start', behavior: 'instant' });
    }
  }, [result.status]);
  const analysisParams = new URLSearchParams({ dataset: datasetId, component: componentId });
  return <aside ref={panel} className="preview panel" aria-label="Component preview">
    <div className="panel-heading"><span><Crosshair size={16} /> COMPONENT PREVIEW</span><button className="icon-button" onClick={onClose} aria-label="Close component preview"><X size={16} /></button></div>
    {result.status === 'loading' && <LoadingState label="Loading component…" />}
    {result.status === 'error' && <ErrorState message={result.message} retry={result.retry} />}
    {result.status === 'success' && <>
      <div className="preview-identity"><span className="chip-icon"><Box size={26} strokeWidth={1.4} /></span><span className="eyebrow">SELECTED COMPONENT</span><h2>{result.data.component_id}</h2><span className="lot-label">{result.data.lot_id}</span></div>
      <div className="preview-body">
        <div className="section-heading"><h3>Observed measurements</h3><span>µA</span></div>
        <div className="measurement-track">
          <div className="measurement"><span className="time-marker" /><div><span className="measurement-label">0h <span>Initial observation</span></span><strong>{formatLeakage(result.data.leakage_0h)}<small>µA</small></strong></div></div>
          <div className="measurement"><span className="time-marker filled" /><div><span className="measurement-label">24h <span>Early burn-in</span></span><strong>{formatLeakage(result.data.leakage_24h)}<small>µA</small></strong></div></div>
        </div>
        <div className="provenance"><Check size={15} /><p>Source observations<span>Retrieved from the selected dataset. No analytical assessment has been run.</span></p></div>
        <Link className="button primary analyze-button" to={`/analysis?${analysisParams}`}>Analyze with Sentinel<ArrowRight size={16} /></Link>
        <p className="action-note">Continue to the analysis workspace.<br />Execution will be available in a later phase.</p>
      </div>
    </>}
  </aside>;
}

export function EmptyPreview() {
  return <aside className="preview panel empty-preview" aria-label="Component preview">
    <div className="panel-heading"><span><Crosshair size={16} /> COMPONENT PREVIEW</span></div>
    <div className="empty-preview-content"><div className="target-graphic"><Crosshair size={40} strokeWidth={1} /></div><h2>Select a component</h2><p>Inspect its lot identity and observed leakage before moving to analysis.</p><span className="keyboard-hint">Choose a component from the table</span></div>
    <div className="preview-note"><span className="tiny-label">OBSERVATION WINDOW</span><strong>0h <span>→</span> 24h</strong><p>Early burn-in measurements only.</p></div>
  </aside>;
}
