import { useCallback } from 'react';
import { Box } from 'lucide-react';
import { sentinelApi, type ComponentObservation } from '../../api/client';
import type { InvestigationSelection, WorkflowState } from '../../api/investigation';
import { useResource } from '../../hooks/useResource';
import { measurement } from './presentation';

export function InputContext({ selection, observed, workflow }: { selection: InvestigationSelection; observed?: ComponentObservation; workflow?: WorkflowState }) {
  const load = useCallback((signal: AbortSignal) => observed ? Promise.resolve(observed) : sentinelApi.component(selection.dataset_id, selection.component_id, signal), [selection.dataset_id, selection.component_id, observed]);
  const resource = useResource(load);
  const source = workflow?.raw_data ?? (resource.status === 'success' ? resource.data : undefined);
  const lot = workflow ? workflow.lot_id : resource.status === 'success' ? resource.data.lot_id : null;
  return <section className="panel investigation-inputs" aria-label="Observed component inputs">
    <div className="input-identity"><Box size={25} /><div><span className="tiny-label">COMPONENT / OBSERVED INPUT</span><strong>{selection.component_id}</strong><span>{lot ?? 'Lot unavailable'}</span></div></div>
    <div><span className="tiny-label">LEAKAGE · 0h</span><strong>{measurement(source?.leakage_0h)} <small>µA</small></strong></div>
    <div><span className="tiny-label">LEAKAGE · 24h</span><strong>{measurement(source?.leakage_24h)} <small>µA</small></strong></div>
    <div className="input-source"><span className="tiny-label">SOURCE DATASET</span><code>{selection.dataset_id}</code><span className="neutral-tag">Observed · not predicted</span></div>
    {!workflow && resource.status === 'error' && <div className="input-error" role="alert">{resource.message}<button className="text-button" onClick={resource.retry}>Reload observations</button></div>}
  </section>;
}
