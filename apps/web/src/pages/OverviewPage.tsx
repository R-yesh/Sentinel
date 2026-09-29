import { ArrowRight, Database, Layers3, ScanLine } from 'lucide-react';
import { Link } from 'react-router-dom';

export function OverviewPage() {
  return <div className="workspace-page overview-page">
    <div className="eyebrow">SENTINEL / ENGINEERING WORKSPACE</div>
    <h1>Reliability starts<br />with the observations<span className="heading-dot">.</span></h1>
    <p className="overview-lead">A workspace for inspecting semiconductor burn-in measurements and preparing component-level reliability investigations.</p>
    <Link to="/dataset" className="button primary">Open dataset workspace <ArrowRight size={17} /></Link>
    <div className="overview-grid">
      <div className="panel overview-card"><Database size={25} /><span className="tiny-label">01 / AVAILABLE NOW</span><h2>Explore the dataset</h2><p>Find components and manufacturing lots. Inspect observed leakage at 0h and 24h.</p></div>
      <div className="panel overview-card"><ScanLine size={25} /><span className="tiny-label">02 / AVAILABLE NOW</span><h2>Inspect a component</h2><p>Keep component identity, lot context, and source measurements in view.</p></div>
      <div className="panel overview-card"><Layers3 size={25} /><span className="tiny-label">03 / AVAILABLE NOW</span><h2>Follow the evidence</h2><p>Run Sentinel, inspect each agent’s evidence, and review the final engineering disposition.</p></div>
    </div>
    <p className="demo-note">SIH demonstration system · Synthetic burn-in dataset · Not an official ISRO production system</p>
  </div>;
}
