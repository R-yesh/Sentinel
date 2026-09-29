import { ArrowLeft, Workflow } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { DATASET_ID } from '../api/client';
import { useInvestigationSession } from '../features/investigation/InvestigationSession';
import { InvestigationWorkspace } from '../features/investigation/InvestigationWorkspace';
import '../features/investigation/investigation.css';

export function AnalysisPage() {
  const [params] = useSearchParams();
  const { run } = useInvestigationSession();
  const component = params.get('component');
  const dataset = params.get('dataset');
  const hasSelectionParams = params.has('component') || params.has('dataset');
  const selection = hasSelectionParams
    ? component?.trim() && dataset === DATASET_ID ? { component_id: component, dataset_id: dataset } : null
    : run?.selection;
  if (selection) return <InvestigationWorkspace key={`${selection.dataset_id}/${selection.component_id}`} selection={selection} />;
  return <div className="workspace-page">
    <div className="eyebrow">ANALYSIS / INVESTIGATION WORKSPACE</div><h1>Follow the evidence<span className="heading-dot">.</span></h1>
    <section className="panel analysis-placeholder"><span className="placeholder-icon"><Workflow size={32} strokeWidth={1.4} /></span><h2>Select a component to investigate</h2><p>{hasSelectionParams ? 'This link does not identify a supported dataset and component. Select a component from the dataset workspace.' : 'Choose a component from the dataset, inspect its observed inputs, then run the Sentinel evidence pipeline.'}</p>
      <Link to="/dataset" className="button primary"><ArrowLeft size={16} />Open dataset workspace</Link>
    </section>
  </div>;
}
