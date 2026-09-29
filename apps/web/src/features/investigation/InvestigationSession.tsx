import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import { sentinelApi, type ComponentObservation } from '../../api/client';
import type { InvestigationResult, InvestigationSelection } from '../../api/investigation';

type RunBase = { selection: InvestigationSelection; observed?: ComponentObservation; requestId: number };
export type InvestigationRun = RunBase & (
  | { status: 'running' }
  | { status: 'error'; message: string }
  | { status: 'success'; result: InvestigationResult }
);
type Session = { run: InvestigationRun | null; start: (selection: InvestigationSelection, observed?: ComponentObservation) => void };
const Context = createContext<Session | null>(null);

/** One current investigation in tab memory. POSTs originate only from user actions. */
export function InvestigationSession({ children }: { children: ReactNode }) {
  const [run, setRun] = useState<InvestigationRun | null>(null);
  const current = useRef<InvestigationRun | null>(null);
  const sequence = useRef(0);
  const start = useCallback((selection: InvestigationSelection, observed?: ComponentObservation) => {
    if (current.current?.status === 'running' && current.current.selection.dataset_id === selection.dataset_id && current.current.selection.component_id === selection.component_id) return;
    const next: InvestigationRun = { selection, observed, requestId: ++sequence.current, status: 'running' };
    current.current = next;
    setRun(next);
    sentinelApi.investigate(selection).then(
      (result) => {
        if (sequence.current !== next.requestId) return;
        const done: InvestigationRun = { ...next, status: 'success', result };
        current.current = done; setRun(done);
      },
      (error: unknown) => {
        if (sequence.current !== next.requestId) return;
        const failed: InvestigationRun = { ...next, status: 'error', message: error instanceof Error ? error.message : 'Investigation request failed.' };
        current.current = failed; setRun(failed);
      },
    );
  }, []);
  return <Context.Provider value={{ run, start }}>{children}</Context.Provider>;
}

export function useInvestigationSession() {
  const session = useContext(Context);
  if (!session) throw new Error('Investigation session provider is required.');
  return session;
}
