import { ArrowLeft, Workflow } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { DATASET_ID } from '../api/client';

export function AnalysisPage() {
  const [params] = useSearchParams();
  const component = params.get('component');
  const dataset = params.get('dataset');
  const selected = component && dataset === DATASET_ID;
  const back = selected ? `/dataset?${new URLSearchParams({ component })}` : '/dataset';
  return <div className="workspace-page">
    <div className="eyebrow">ANALYSIS / WORKSPACE FOUNDATION</div><h1>Analysis workspace<span className="heading-dot">.</span></h1>
    <section className="panel analysis-placeholder"><span className="placeholder-icon"><Workflow size={32} strokeWidth={1.4} /></span><span className="outline-badge">COMING IN A LATER PHASE</span><h2>{selected ? 'Component selection ready' : 'From observations to evidence'}</h2><p>Investigation execution and evidence visualization are not available in this phase. No investigation has been started.</p>
      {selected && <dl className="selection-summary"><div><dt>Dataset</dt><dd>{dataset}</dd></div><div><dt>Selected component ID</dt><dd>{component}</dd></div></dl>}
      <Link to={back} className="button secondary"><ArrowLeft size={16} />Back to dataset</Link>
    </section>
  </div>;
}
