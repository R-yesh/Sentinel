import { AlertCircle, LoaderCircle } from 'lucide-react';

export function LoadingState({ label }: { label: string }) {
  return <div className="state-message" role="status"><LoaderCircle className="spinner" size={22} /><span>{label}</span></div>;
}

export function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  return <div className="state-message error-state" role="alert">
    <AlertCircle size={24} /><strong>Unable to load data</strong><p>{message}</p>
    <button className="button secondary" onClick={retry}>Try again</button>
  </div>;
}

export function formatLeakage(value: number | null): string {
  return value === null || !Number.isFinite(value) ? 'Unavailable' : value.toFixed(4);
}
