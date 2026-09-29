import { StrictMode } from 'react';
import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { parseInvestigation, type Decision } from '../api/investigation';
import { Disposition } from '../features/investigation/Disposition';
import { executionFixture } from './executionFixture';

const selection = { dataset_id: 'synthetic-burnin', component_id: 'TEST001' };
const observed = { component_id: 'TEST001', lot_id: 'LOT-TEST', leakage_0h: 10, leakage_24h: 10.2 };
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
// Test-only examples matching the API envelope. No fixture is imported by application code.
function result(decision: Decision = 'PASS', component = 'TEST001') {
  return { dataset_id: selection.dataset_id, workflow_execution: executionFixture(), workflow: {
    workflow_id: `workflow-${component}`, component_id: component, lot_id: 'LOT-TEST',
    status: decision === 'REVIEW' ? 'needs_review' : 'completed', raw_data: observed, lot_context: null,
    final_decision: decision, explanation: 'Engineering reasoning returned by Sentinel.',
    findings: [{ agent: 'lot_intelligence', component_id: component, finding_type: 'lot_assessment', severity: 'medium', summary: 'Lot evidence recorded.', evidence: ['Peer population considered.'], metadata: { robust_z_score: 'Infinity' } }],
    agent_outputs: {
      data_forensics: { passed: true, missing_fields: [] },
      drift_intelligence: { passed: true, percentage_change: 2, early_slope: 0.0083, predicted_168h: 11.4, prediction_uncertainty: 0.7 },
      lot_intelligence: { passed: true, lot_population_size: 49, lot_median: 10.1, lot_mad: 0, robust_z_score: 'Infinity', percentile: 0.8 },
      latent_defect: { assessment: 'LOW_CONCERN', signal_count: 0, signals: {} },
      adversarial_qa: { review: { challenged_assessment: 'LOW_CONCERN', challenges: [], unresolved_conflict: false } },
      reliability_judge: { decision, reason_code: 'TEST_REASON', reasoning: 'Judge reasoning.', supporting_evidence: ['Evidence supplied by judge.'], unresolved_concerns: [] },
      explanation: { headline: 'Engineering disposition', summary: 'Explanation summary.', key_evidence: ['Early observations.'], adversarial_context: [], decision_reasoning: 'Decision reasoning.', recommended_action: 'Continue the specified engineering process.' },
    },
  } };
}
function api(post: (body: typeof selection) => Response | Promise<Response>) {
  const mock = vi.fn(async (input: string, init?: RequestInit) => {
    if (input.endsWith('/investigations')) return post(JSON.parse(init?.body as string));
    if (input.endsWith('/health')) return response({ status: 'ok', service: 'sentinel-api' });
    if (/\/components\//.test(input)) return response({ ...observed, component_id: input.split('/').at(-1) });
    return response({ dataset_id: selection.dataset_id, items: [observed, { ...observed, component_id: 'TEST002' }], total: 2, page: 1, page_size: 25 });
  });
  vi.stubGlobal('fetch', mock);
  return mock;
}
function mount(route = '/analysis?dataset=synthetic-burnin&component=TEST001') {
  render(<StrictMode><MemoryRouter initialEntries={[route]}><App /></MemoryRouter></StrictMode>);
}

describe('Investigation workspace', () => {
  it('starts only on action, sends one POST in StrictMode, and exposes returned agent evidence', async () => {
    let finish!: (value: Response) => void;
    const mock = api(() => new Promise<Response>((resolve) => { finish = resolve; }));
    const user = userEvent.setup();
    mount();
    expect(mock.mock.calls.filter(([url]) => url.endsWith('/investigations'))).toHaveLength(0);
    await user.click(screen.getByRole('button', { name: 'Run investigation' }));
    expect(screen.getByText('Sentinel is investigating TEST001')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Inspect Drift Intelligence' })).toBeDisabled();
    expect(screen.queryByRole('region', { name: 'Reliability disposition' })).not.toBeInTheDocument();
    const posts = mock.mock.calls.filter(([url]) => url.endsWith('/investigations'));
    expect(posts).toHaveLength(1);
    expect(posts[0][1]?.method).toBe('POST');
    expect(JSON.parse(posts[0][1]?.body as string)).toEqual(selection);
    await act(async () => { finish(response(result())); });
    expect(within(await screen.findByRole('region', { name: 'Reliability disposition' })).getByRole('heading', { name: 'PASS' })).toBeInTheDocument();
    expect(screen.getByText('INDEPENDENT ANALYSES · SEPARATE STATE COPIES')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Skip to result' }));
    expect(screen.getByText('Execution replay · normalized visual time; labels show real duration')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Inspect Drift Intelligence' }));
    expect(within(screen.getByRole('region', { name: 'Agent details' })).getByText('11.4000')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Inspect Lot Intelligence' }));
    const details = screen.getByRole('region', { name: 'Agent details' });
    expect(within(details).getByText('+∞', { selector: 'dd' })).toBeInTheDocument();
    expect(within(details).getByText('Lot evidence recorded.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Inspect Adversarial QA' }));
    expect(screen.getByRole('heading', { name: 'Adversarial challenges' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Final disposition' }));
    expect(screen.getByText('Continue the specified engineering process.')).toBeInTheDocument();
  });

  it('shows API failure without a fabricated result, then retries successfully', async () => {
    let attempts = 0;
    api(() => ++attempts === 1 ? response({ detail: 'Pipeline execution failed.' }, 502) : response(result('REVIEW')));
    const user = userEvent.setup(); mount();
    await user.click(screen.getByRole('button', { name: 'Run investigation' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Pipeline execution failed.');
    expect(screen.queryByRole('region', { name: 'Reliability disposition' })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Retry investigation' }));
    expect(within(await screen.findByRole('region', { name: 'Reliability disposition' })).getByRole('heading', { name: 'REVIEW' })).toBeInTheDocument();
    expect(attempts).toBe(2);
  });

  it('does not replace a newer component with a late response from the previous investigation', async () => {
    let first!: (value: Response) => void;
    api((body) => body.component_id === 'TEST001' ? new Promise<Response>((resolve) => { first = resolve; }) : response(result('REJECT', 'TEST002')));
    const user = userEvent.setup(); mount();
    await user.click(screen.getByRole('button', { name: 'Run investigation' }));
    await user.click(screen.getByRole('link', { name: 'Back to dataset' }));
    await user.click(await screen.findByRole('button', { name: 'TEST002' }));
    await user.click(await screen.findByRole('link', { name: 'Analyze with Sentinel' }));
    const disposition = await screen.findByRole('region', { name: 'Reliability disposition' });
    expect(within(disposition).getByText('TEST002')).toBeInTheDocument();
    await act(async () => { first(response(result())); });
    expect(within(disposition).getByRole('heading', { name: 'REJECT' })).toBeInTheDocument();
    expect(within(disposition).queryByText('TEST001')).not.toBeInTheDocument();
  });

  it('keeps a validation stop distinct from a REVIEW decision and tolerates partial evidence', async () => {
    api(() => response({ dataset_id: selection.dataset_id, workflow: { workflow_id: 'stopped', component_id: 'TEST001', status: 'needs_review', final_decision: null, findings: null, agent_outputs: { data_forensics: { passed: false, missing_fields: ['leakage_0h'] }, drift_intelligence: null } } }));
    const user = userEvent.setup(); mount();
    await user.click(screen.getByRole('button', { name: 'Run investigation' }));
    const disposition = await screen.findByRole('region', { name: 'Reliability disposition' });
    expect(within(disposition).getByRole('heading', { name: 'No decision issued' })).toBeInTheDocument();
    expect(within(disposition).getByText(/not a judge-issued REVIEW/)).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('raw_data was missing or malformed');
    expect(screen.getByRole('button', { name: 'Inspect Drift Intelligence' })).toHaveTextContent('Execution unknown');
    await user.click(screen.getByRole('button', { name: 'Inspect Data Forensics' }));
    expect(screen.getByText('leakage_0h')).toBeInTheDocument();
  });

  it('rejects malformed envelopes and mismatched component identities', () => {
    expect(() => parseInvestigation({}, selection)).toThrow(/workflow is missing/);
    expect(() => parseInvestigation(result('PASS', 'OTHER'), selection)).toThrow(/identity/);
  });

  it.each(['PASS', 'REVIEW', 'REJECT'] as const)('renders the authoritative %s disposition with its evidence', (decision) => {
    const parsed = parseInvestigation(result(decision), selection);
    render(<Disposition workflow={parsed.workflow} />);
    expect(screen.getByRole('heading', { name: decision })).toBeInTheDocument();
    expect(screen.getByText('TEST_REASON')).toBeInTheDocument();
    expect(screen.getByText('Evidence supplied by judge.')).toBeInTheDocument();
    expect(screen.getByText('Engineering reasoning returned by Sentinel.')).toBeInTheDocument();
  });
});
