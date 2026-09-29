import { parseInvestigation, type InvestigationSelection } from './investigation';

/** These types mirror the Phase 1 API's observed-data responses. */
export interface ComponentObservation {
  component_id: string;
  lot_id: string;
  leakage_0h: number | null;
  leakage_24h: number | null;
}

export interface ComponentPage {
  dataset_id: string;
  items: ComponentObservation[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthResponse {
  status: string;
  service: string;
}

// Phase 1 exposes one known dataset, not a dataset-discovery endpoint.
export const DATASET_ID = 'synthetic-burnin';
const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, signal?: AbortSignal, options: { body?: unknown; timeoutMs?: number } = {}): Promise<T> {
  const timeout = AbortSignal.timeout(options.timeoutMs ?? 20_000);
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method: options.body === undefined ? 'GET' : 'POST',
      headers: { Accept: 'application/json', ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }) },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(timeout.aborted
      ? 'The API took too long to respond. Please try again.'
      : 'Cannot reach Sentinel API. Check that the backend is running.');
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status}). Please try again.`,
      response.status,
    );
  }
  try {
    return await response.json() as T;
  } catch {
    throw new ApiError('The API returned an unreadable response.');
  }
}

export const sentinelApi = {
  components: (datasetId: string, search: string, page: number, pageSize: number, signal?: AbortSignal) => {
    const params = new URLSearchParams({ search, page: String(page), page_size: String(pageSize) });
    return request<ComponentPage>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/components?${params}`, signal);
  },
  component: (datasetId: string, componentId: string, signal?: AbortSignal) =>
    request<ComponentObservation>(`/api/v1/datasets/${encodeURIComponent(datasetId)}/components/${encodeURIComponent(componentId)}`, signal),
  health: (signal?: AbortSignal) => request<HealthResponse>('/health', signal),
  investigate: async (selection: InvestigationSelection) => {
    // Three sequential structured LLM calls can outlast the browsing timeout.
    const response = await request<unknown>('/api/v1/investigations', undefined, { body: selection, timeoutMs: 600_000 });
    return parseInvestigation(response, selection);
  },
};
