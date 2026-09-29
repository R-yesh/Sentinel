import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import type { ComponentObservation } from '../api/client';

// Contract fixtures only; the application has no bundled measurement data.
const first: ComponentObservation = { component_id: 'TEST001', lot_id: 'LOT-TEST', leakage_0h: 10.1, leakage_24h: 10.3 };
const second: ComponentObservation = { component_id: 'TEST002', lot_id: 'LOT-TEST', leakage_0h: 9.8, leakage_24h: 10.1 };
const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } });
const page = (items = [first, second], total = 26, current = 1) => ({ dataset_id: 'synthetic-burnin', items, total, page: current, page_size: 25 });

function mockApi(override?: (url: URL) => Response | Promise<Response> | undefined) {
  const fetchMock = vi.fn((input: string) => {
    const url = new URL(input, 'http://localhost');
    const custom = override?.(url);
    if (custom) return Promise.resolve(custom);
    if (url.pathname === '/health') return Promise.resolve(response({ status: 'ok', service: 'sentinel-api' }));
    if (url.pathname.endsWith('/TEST001')) return Promise.resolve(response(first));
    if (url.pathname.endsWith('/TEST002')) return Promise.resolve(response(second));
    return Promise.resolve(response(page()));
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function mount(route = '/dataset') {
  return render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);
}

describe('Dataset workspace', () => {
  it('requests search and pagination from the API and preserves the unfiltered count', async () => {
    const fetchMock = mockApi((url) => {
      if (url.searchParams.get('search') === 'TEST0030') return response(page([{ ...first, component_id: 'TEST0030' }], 1));
      if (url.searchParams.get('page') === '2') return response(page([{ ...second, component_id: 'TEST026' }], 26, 2));
    });
    const user = userEvent.setup();
    mount();
    await screen.findByRole('button', { name: 'TEST001' });
    await user.click(screen.getByRole('button', { name: 'Next page' }));
    await screen.findByRole('button', { name: 'TEST026' });
    expect(fetchMock.mock.calls.some(([url]) => new URL(url, 'http://localhost').searchParams.get('page') === '2')).toBe(true);
    await user.type(screen.getByRole('textbox', { name: 'Search component or lot ID' }), 'TEST0030');
    await user.click(screen.getByRole('button', { name: /^Search$/ }));
    await screen.findByRole('button', { name: 'TEST0030' });
    expect(screen.getByText('1 matching component')).toBeInTheDocument();
    expect(within(screen.getByRole('region', { name: 'Dataset summary' })).getByText('26')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => {
      const query = new URL(url, 'http://localhost').searchParams;
      return query.get('search') === 'TEST0030' && query.get('page') === '1';
    })).toBe(true);
    expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled();
  });

  it('fetches component detail and carries selection into analysis without executing it', async () => {
    const fetchMock = mockApi();
    const user = userEvent.setup();
    mount();
    await user.click(await screen.findByRole('button', { name: 'TEST001' }));
    const preview = screen.getByRole('complementary', { name: 'Component preview' });
    await within(preview).findByRole('heading', { name: 'TEST001' });
    expect(within(preview).getByText('10.1000')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => url.endsWith('/components/TEST001'))).toBe(true);
    await user.click(screen.getByRole('link', { name: 'Analyze with Sentinel' }));
    expect(await screen.findByRole('heading', { name: 'Component selection ready' })).toBeInTheDocument();
    expect(screen.getByText('TEST001')).toBeInTheDocument();
    expect(screen.getByText(/No investigation has been started/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.every(([url]) => !url.includes('/investigations'))).toBe(true);
  });

  it('ignores a late detail response after a newer selection', async () => {
    let resolveFirst!: (value: Response) => void;
    mockApi((url) => url.pathname.endsWith('/TEST001') ? new Promise<Response>((resolve) => { resolveFirst = resolve; }) : undefined);
    const user = userEvent.setup();
    mount();
    await user.click(await screen.findByRole('button', { name: 'TEST001' }));
    await user.click(screen.getByRole('button', { name: 'TEST002' }));
    const preview = screen.getByRole('complementary', { name: 'Component preview' });
    await within(preview).findByRole('heading', { name: 'TEST002' });
    await act(async () => { resolveFirst(response(first)); });
    expect(within(preview).getByRole('heading', { name: 'TEST002' })).toBeInTheDocument();
    expect(within(preview).queryByRole('heading', { name: 'TEST001' })).not.toBeInTheDocument();
  });

  it('shows a loading state then a useful empty search state', async () => {
    let resolveSearch!: (value: Response) => void;
    mockApi((url) => url.searchParams.get('search') === 'missing' ? new Promise<Response>((resolve) => { resolveSearch = resolve; }) : undefined);
    mount('/dataset?search=missing');
    expect(screen.getByText('Loading observed measurements…')).toBeInTheDocument();
    await act(async () => { resolveSearch(response(page([], 0))); });
    expect(await screen.findByRole('heading', { name: 'No matching components' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled();
  });

  it('shows API errors and retries the failed request', async () => {
    let fail = true;
    mockApi((url) => url.pathname.endsWith('/components') && url.searchParams.get('page_size') === '25' && fail
      ? response({ detail: 'Synthetic dataset is unavailable or invalid.' }, 503) : undefined);
    const user = userEvent.setup();
    mount();
    expect(await screen.findByRole('alert')).toHaveTextContent('Synthetic dataset is unavailable or invalid.');
    fail = false;
    await user.click(screen.getByRole('button', { name: 'Try again' }));
    await screen.findByRole('button', { name: 'TEST001' });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('renders unavailable observations without inventing a zero value', async () => {
    mockApi((url) => url.pathname.endsWith('/components') ? response(page([{ ...first, leakage_0h: null }], 1)) : undefined);
    mount();
    expect(await screen.findByRole('cell', { name: 'Unavailable' })).toBeInTheDocument();
    expect(screen.queryByRole('cell', { name: '0.0000' })).not.toBeInTheDocument();
  });

  it('restores selection from a direct dataset URL and reports detail errors', async () => {
    mockApi((url) => url.pathname.endsWith('/UNKNOWN') ? response({ detail: "Component 'UNKNOWN' was not found." }, 404) : undefined);
    mount('/dataset?component=UNKNOWN');
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent("Component 'UNKNOWN' was not found."));
    expect(screen.queryByRole('link', { name: 'Analyze with Sentinel' })).not.toBeInTheDocument();
  });
});
