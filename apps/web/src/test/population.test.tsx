import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import { App } from '../App';
import type { PopulationResponse } from '../api/population';
import { ScreeningComparison } from '../features/population/ScreeningComparison';

const fixture: PopulationResponse = {
  dataset_id: 'synthetic-burnin', snapshot_id: 'test-snapshot', method: 'test-method', early_drift_threshold_percent: 6,
  summary: { total: 2, lots: 1, screened: 2, unassessed: 0, candidates: 1, no_screening_signal: 1, significant_drift: 1, high_side_lot: 0 },
  comparison: { status: 'unconfigured', limit_ua: null, rule: 'Observed leakage_24h > limit', comparable: 2, excluded: 0, conventional_only: null, sentinel_only: null, both: null, neither: null },
  lots: [{ lot_id: 'LOT-TEST', total: 2, screened: 2, candidates: 1, unassessed: 0 }],
  drift_histogram: [{ lower: 0, upper: 10, count: 2 }],
  components: [
    { component_id: 'TEST001', lot_id: 'LOT-TEST', leakage_0h: 10, leakage_24h: 11, percentage_change: 10, early_slope: 1 / 24, lot_evidence: 'TYPICAL', robust_z_score: 0.4, candidate: true, reasons: ['significant_early_drift'], issue: null, conventional_flag: null },
    { component_id: 'TEST002', lot_id: 'LOT-TEST', leakage_0h: 10, leakage_24h: 10, percentage_change: 0, early_slope: 0, lot_evidence: 'TYPICAL', robust_z_score: 0, candidate: false, reasons: [], issue: null, conventional_flag: null },
  ],
};
const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });
function api(failure = false) {
  const mock = vi.fn((url: string, options?: RequestInit) => {
    if (url.endsWith('/health')) return Promise.resolve(response({ status: 'ok' }));
    if (url.endsWith('/investigations')) return new Promise<Response>(() => {});
    if (url.endsWith('/population')) return Promise.resolve(failure ? response({ detail: 'Dataset unavailable.' }, 503) : response(fixture));
    return Promise.resolve(response(fixture.components[0]));
  });
  vi.stubGlobal('fetch', mock);
  return mock;
}
it('loads population without investigations, filters the full returned population, and investigates through Phase 3', async () => {
  const fetch = api(); const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/']}><App /></MemoryRouter>);
  expect(await screen.findByRole('heading', { name: 'Reliability command center.' })).toBeInTheDocument();
  expect(await screen.findByText('Conventional reference not configured')).toBeInTheDocument();
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/investigations'))).toBe(false);
  expect(screen.getByRole('button', { name: 'Investigate TEST001' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Investigate TEST002' })).not.toBeInTheDocument();
  await user.selectOptions(screen.getByRole('combobox', { name: 'Screening evidence filter' }), 'all');
  expect(screen.getByRole('button', { name: 'Investigate TEST002' })).toBeInTheDocument();
  await user.type(screen.getByRole('textbox', { name: 'Search population component' }), 'TEST001');
  expect(screen.queryByRole('button', { name: 'Investigate TEST002' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Investigate TEST001' }));
  expect(await screen.findByText('Sentinel is investigating TEST001')).toBeInTheDocument();
  const posts = fetch.mock.calls.filter(([url]) => url.endsWith('/investigations'));
  expect(posts).toHaveLength(1);
  expect(JSON.parse(posts[0][1]?.body as string)).toEqual({ dataset_id: 'synthetic-burnin', component_id: 'TEST001' });
});

it('presents configured overlap using backend counts, without a missed-defect claim', () => {
  render(<ScreeningComparison data={{ ...fixture, comparison: { ...fixture.comparison, status: 'configured', limit_ua: 10.5, conventional_only: 0, sentinel_only: 0, both: 1, neither: 1 } }} />);
  const panel = screen.getByRole('region', { name: 'Conventional versus Sentinel screening' });
  expect(within(panel).getByText(/24h leakage > 10.5 µA/)).toBeInTheDocument();
  expect(within(panel).getByText(/not a confirmed missed defect/)).toBeInTheDocument();
  expect(within(panel).getByText('Both methods')).toBeInTheDocument();
});

it('reports population API failures and provides retry', async () => {
  api(true);
  render(<MemoryRouter initialEntries={['/overview']}><App /></MemoryRouter>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Dataset unavailable.');
  api();
  await userEvent.setup().click(screen.getByRole('button', { name: 'Try again' }));
  expect(await screen.findByRole('button', { name: 'Investigate TEST001' })).toBeInTheDocument();
});
