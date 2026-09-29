import { useEffect, useReducer, useState } from 'react';

type Resource<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: T };

/** Callers memoize load; abort and ignore stale requests when selection changes. */
export function useResource<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [resource, setResource] = useState<Resource<T>>({ status: 'loading' });
  const [attempt, retry] = useReducer((value: number) => value + 1, 0);
  useEffect(() => {
    const controller = new AbortController();
    setResource({ status: 'loading' });
    load(controller.signal).then(
      (data) => { if (!controller.signal.aborted) setResource({ status: 'success', data }); },
      (error: unknown) => {
        if (!controller.signal.aborted) setResource({
          status: 'error', message: error instanceof Error ? error.message : 'Request failed. Please try again.',
        });
      },
    );
    return () => controller.abort();
  }, [load, attempt]);
  return { ...resource, retry };
}
