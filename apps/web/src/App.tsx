import { Navigate, Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { DatasetPage } from './features/dataset/DatasetPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { OverviewPage } from './pages/OverviewPage';

export function App() {
  return <Routes><Route element={<Shell />}>
    <Route index element={<Navigate to="/dataset" replace />} />
    <Route path="dataset" element={<DatasetPage />} />
    <Route path="overview" element={<OverviewPage />} />
    <Route path="analysis" element={<AnalysisPage />} />
    <Route path="*" element={<Navigate to="/dataset" replace />} />
  </Route></Routes>;
}
