import { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, Database, FlaskConical, LayoutDashboard, PanelLeftClose, PanelLeftOpen, Radio, X } from 'lucide-react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { sentinelApi } from '../api/client';

function HealthIndicator() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  useEffect(() => {
    let controller: AbortController;
    const check = () => {
      controller?.abort();
      controller = new AbortController();
      const signal = controller.signal;
      sentinelApi.health(signal).then(
        (result) => { if (!signal.aborted) setStatus(result.status === 'ok' ? 'online' : 'offline'); },
        () => { if (!signal.aborted) setStatus('offline'); },
      );
    };
    check();
    const interval = window.setInterval(check, 30_000);
    return () => { controller.abort(); window.clearInterval(interval); };
  }, []);
  return <span className={`health ${status}`} role="status" title="API reachability checked every 30 seconds. This does not verify model or Gemini readiness.">
    <span className="status-dot" />API {status === 'online' ? 'connected' : status === 'offline' ? 'unavailable' : 'connecting'}
  </span>;
}

export function Shell() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  useEffect(() => { setOpen(false); }, [location.pathname]);
  const section = location.pathname.startsWith('/analysis') ? 'Analysis' : location.pathname === '/evaluation' ? 'Evaluation' : location.pathname === '/overview' ? 'Overview' : 'Dataset workspace';
  useEffect(() => { document.title = `${section} · Sentinel`; }, [section]);
  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to workspace</a>
    {open && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'is-open' : ''}`} aria-label="Application navigation">
      <NavLink to="/dataset" className="brand" aria-label="Sentinel dataset workspace">
        <img src="/sentinel.svg" alt="" /><span>SENTINEL<small>RELIABILITY INTELLIGENCE</small></span>
      </NavLink>
      <button className="icon-button mobile-close" aria-label="Close navigation" onClick={() => setOpen(false)}><X size={18} /></button>
      <div className="nav-label">WORKSPACE</div>
      <nav>
        <NavLink to="/overview"><LayoutDashboard size={18} />Overview</NavLink>
        <NavLink to="/dataset"><Database size={18} />Dataset<span className="nav-marker" /></NavLink>
        <NavLink to="/analysis"><Activity size={18} />Analysis<span className="nav-marker" /></NavLink>
        <NavLink to="/evaluation"><FlaskConical size={18} />Evaluation</NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="mission-mark"><FlaskConical size={18} /><span>SIH demonstration<small>Semiconductor burn-in</small></span></div>
        <div className="sidebar-foot"><span className="status-dot" />EARLY OBSERVATIONS<span>0h / 24h</span></div>
      </div>
    </aside>
    <div className="main-column">
      <header className="topbar">
        <div className="breadcrumb"><button className="icon-button mobile-menu" aria-label="Open navigation" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <PanelLeftClose size={19} /> : <PanelLeftOpen size={19} />}</button><span className="desktop-label">Workspace</span><span className="breadcrumb-slash">/</span><strong>{section}</strong></div>
        <div className="topbar-right"><span className="environment"><Radio size={13} />DEMO ENVIRONMENT</span><HealthIndicator /></div>
      </header>
      <main id="main" tabIndex={-1}><Outlet /></main>
      <footer className="app-footer"><span>SENTINEL <span className="footer-divider">/</span> Semiconductor Reliability Intelligence</span><span>Observed evidence first <ArrowUpRight size={12} /></span></footer>
    </div>
  </div>;
}
