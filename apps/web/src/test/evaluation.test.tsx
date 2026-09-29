import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import { App } from '../App';
import type { EvaluationComponent, EvaluationResponse } from '../api/evaluation';
import { EvaluationComparison } from '../features/evaluation/EvaluationComparison';

function component(id: string, label: string, candidate: boolean): EvaluationComponent {
  return { early: { component_id: id, lot_id: 'L1', leakage_0h: 10, leakage_24h: 11, percentage_change: 10, early_slope: 1 / 24, candidate, reasons: candidate ? ['significant_early_drift'] : [], issue: null, conventional_flag: null, lot_evidence: 'TYPICAL', robust_z_score: 0 }, hindsight: { defect_type: label, synthetic_class: label === 'healthy' ? 'healthy' : 'defective', leakage_96h: 123.4567, leakage_168h: 987.6543 }, evaluated: true, comparison_bucket: null };
}
const data: EvaluationResponse = {
  dataset_id: 'synthetic-burnin', evaluation_only: true, snapshot_id: 'test-evaluation', screening_method: 'phase4', healthy_label: 'healthy', defective_labels: ['mild_drift', 'strong_drift', 'latent_defect'],
  summary: { total: 3, evaluated: 3, excluded: 0, unknown_labels: 0, candidates: 1, screening_rate: 100 / 3,
    healthy: { total: 1, evaluated: 1, excluded: 0, flagged: 0, not_flagged: 1, flag_rate: 0 },
    defective: { total: 2, evaluated: 2, excluded: 0, flagged: 1, not_flagged: 1, flag_rate: 50 } },
  by_defect_type: [{ defect_type: 'mild_drift', total: 1, evaluated: 1, excluded: 0, flagged: 0, not_flagged: 1, flag_rate: 0 }, { defect_type: 'strong_drift', total: 1, evaluated: 1, excluded: 0, flagged: 1, not_flagged: 0, flag_rate: 100 }, { defect_type: 'healthy', total: 1, evaluated: 1, excluded: 0, flagged: 0, not_flagged: 1, flag_rate: 0 }],
  signal_overlap: { drift_only: 1, lot_only: 0, both: 0, neither: 2 },
  comparison: { status: 'unconfigured', limit_ua: null, rule: '24h > limit', comparable_defective: 2, excluded_defective: 0, conventional_flagged: null, sentinel_flagged: null, conventional_only: null, sentinel_only: null, both: null, neither: null },
  components: [component('HEALTHY', 'healthy', false), component('MISSED', 'mild_drift', false), component('FLAGGED', 'strong_drift', true)],
};
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
function api(fail = false) {
  const fetch = vi.fn((url: string, options?: RequestInit) => {
    if (url.endsWith('/investigations')) return new Promise<Response>(() => {});
    if (url.endsWith('/evaluation')) return Promise.resolve(fail ? response({ detail: 'Evaluation labels unavailable.' }, 503) : response(data));
    if (url.endsWith('/population')) return Promise.resolve(response({ dataset_id: data.dataset_id, snapshot_id: 'early', method: 'phase4', early_drift_threshold_percent: 6, summary: { total: 3, lots: 1, screened: 3, unassessed: 0, candidates: 1, no_screening_signal: 2, significant_drift: 1, high_side_lot: 0 }, comparison: { status: 'unconfigured' }, components: data.components.map((r) => r.early), lots: [], drift_histogram: [] }));
    return Promise.resolve(response({ status: 'ok' }));
  });
  vi.stubGlobal('fetch', fetch); return fetch;
}
function mount() { render(<MemoryRouter initialEntries={['/evaluation']}><App /></MemoryRouter>); }

it('shows evaluation-only hindsight and unflagged synthetic defects, without running investigations', async () => {
  const fetch = api(); mount();
  expect(await screen.findByText('EVALUATION MODE · HINDSIGHT VISIBLE')).toBeInTheDocument();
  expect(await screen.findByText('Conventional comparison intentionally unavailable')).toBeInTheDocument();
  const table = screen.getByRole('region', { name: 'Retrospective component review' });
  expect(within(table).getByRole('button', { name: 'Investigate MISSED' })).toBeInTheDocument();
  expect(within(table).queryByRole('button', { name: 'Investigate FLAGGED' })).not.toBeInTheDocument();
  expect(within(table).getByText('987.6543')).toBeInTheDocument();
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/investigations'))).toBe(false);
});

it('sends only the Phase 3 selection and early observations when investigating from evaluation', async () => {
  const fetch = api(); const user = userEvent.setup(); mount();
  await user.click(await screen.findByRole('button', { name: 'Investigate MISSED' }));
  expect(await screen.findByText('Sentinel is investigating MISSED')).toBeInTheDocument();
  const posts = fetch.mock.calls.filter(([url]) => url.endsWith('/investigations'));
  expect(posts).toHaveLength(1);
  expect(JSON.parse(posts[0][1]?.body as string)).toEqual({ dataset_id: 'synthetic-burnin', component_id: 'MISSED' });
  const input = screen.getByRole('region', { name: 'Observed component inputs' });
  expect(within(input).getByText('10.0000')).toBeInTheDocument();
  expect(screen.queryByText('987.6543')).not.toBeInTheDocument();
  expect(screen.queryByText('mild_drift')).not.toBeInTheDocument();
  await user.click(screen.getByRole('link', { name: /^Overview$/ }));
  expect(await screen.findByRole('heading', { name: 'Reliability command center.' })).toBeInTheDocument();
  expect(await screen.findByText('Conventional reference not configured')).toBeInTheDocument();
});

it('renders configured defective comparison and exposes its qualification', () => {
  render(<EvaluationComparison data={{ ...data, comparison: { ...data.comparison, status: 'configured', limit_ua: 12, conventional_flagged: 1, sentinel_flagged: 1, both: 0, neither: 0, conventional_only: 1, sentinel_only: 1 } }} />);
  expect(screen.getByText(/24h leakage > 12 µA/)).toBeInTheDocument();
  expect(screen.getByText(/not by the configured conventional 24h rule/)).toBeInTheDocument();
});

it('handles evaluation API errors and retries', async () => {
  api(true); mount();
  expect(await screen.findByRole('alert')).toHaveTextContent('Evaluation labels unavailable.');
  api(); await userEvent.setup().click(screen.getByRole('button', { name: 'Try again' }));
  expect(await screen.findByRole('button', { name: 'Investigate MISSED' })).toBeInTheDocument();
});
