import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { parseExecution } from '../api/execution';
import { type WorkflowState } from '../api/investigation';
import { WorkflowGraph } from '../features/investigation/WorkflowGraph';
import { replayTimeline } from '../features/investigation/replay';
import { executionFixture } from './executionFixture';

const workflow: WorkflowState = { workflow_id: 'test', component_id: 'C', lot_id: 'L', raw_data: {}, lot_context: null, findings: [], agent_outputs: { data_forensics: { passed: true }, drift_intelligence: { passed: false } }, status: 'completed', final_decision: 'PASS', explanation: 'Test explanation' };
afterEach(() => vi.useRealTimers());

it('maps measured intervals without losing overlap or branch finish order', () => {
  const t = replayTimeline(executionFixture())!;
  const [, drift, lot, latent] = t.agents;
  expect(lot.start).toBeLessThan(drift.end!);
  expect(drift.end).toBeLessThan(lot.end!);
  expect(latent.start).toBeGreaterThan(lot.end!);
  expect(t.duration).toBeLessThanOrEqual(6000);
});

it('renders telemetry, parallel nodes, inspection and replay pause/reset/skip', () => {
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'performance'] });
  const onSelect = vi.fn(); const onDisposition = vi.fn(); const execution = executionFixture();
  render(<WorkflowGraph workflow={workflow} execution={execution} running={false} selected={null} onSelect={onSelect} onDisposition={onDisposition} />);
  expect(screen.getByLabelText('Measured execution summary')).toHaveTextContent('4.0 s');
  const drift = screen.getByRole('button', { name: 'Inspect Drift Intelligence' });
  expect(drift).toHaveTextContent('155 ms');
  expect(drift.closest('.parallel-stage')).toContainElement(screen.getByRole('button', { name: 'Inspect Lot Intelligence' }));
  act(() => vi.advanceTimersByTime(400));
  expect(drift).toHaveTextContent('Replay active');
  expect(screen.getByRole('button', { name: 'Inspect Lot Intelligence' })).toHaveTextContent('Replay active');
  fireEvent.click(screen.getByRole('button', { name: 'Pause' }));
  act(() => vi.advanceTimersByTime(2000));
  expect(drift).toHaveTextContent('Replay active');
  fireEvent.click(drift); expect(onSelect).toHaveBeenCalledWith('drift_intelligence');
  fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
  expect(drift).toHaveTextContent('Replay pending');
  fireEvent.click(screen.getByRole('button', { name: /^Replay$/ }));
  act(() => vi.advanceTimersByTime(6500));
  expect(drift).toHaveTextContent('Completed'); // passed:false is analytical, not an execution error.
  expect(drift).not.toHaveTextContent('attention');
  fireEvent.click(screen.getByRole('button', { name: 'Skip to result' }));
  fireEvent.click(screen.getByRole('button', { name: /RETURNED DISPOSITION/ }));
  expect(onDisposition).toHaveBeenCalled();
  expect(screen.getByRole('button', { name: /RETURNED DISPOSITION/ })).toHaveTextContent('PASS');
});

it('shows validation attention and all later agents as not executed, still inspectable', () => {
  const execution = executionFixture();
  execution.total_duration_ms = 20;
  execution.agents = execution.agents.map((r, i) => i === 0 ? r : { ...r, status: 'not_executed', started_at: null, completed_at: null, start_offset_ms: null, end_offset_ms: null, duration_ms: null });
  const onSelect = vi.fn();
  render(<WorkflowGraph workflow={{ ...workflow, final_decision: null, status: 'needs_review', agent_outputs: { data_forensics: { passed: false } } }} execution={execution} running={false} selected={null} onSelect={onSelect} />);
  fireEvent.click(screen.getByRole('button', { name: 'Skip to result' }));
  expect(screen.getByRole('button', { name: 'Inspect Data Forensics' })).toHaveTextContent('Completed · attention');
  const lot = screen.getByRole('button', { name: 'Inspect Lot Intelligence' });
  expect(lot).toHaveTextContent('Not executed');
  fireEvent.click(lot); expect(onSelect).toHaveBeenCalledWith('lot_intelligence');
  expect(screen.getByRole('button', { name: /RETURNED DISPOSITION/ })).toHaveTextContent('No decision issued');
});

it('rejects malformed timing independently and falls back to static evidence', () => {
  expect(parseExecution(undefined)).toBeNull();
  const bad = executionFixture(); bad.agents[1].duration_ms = -10;
  expect(parseExecution(bad)).toBeNull();
  const duplicate = executionFixture(); duplicate.agents[1] = duplicate.agents[0];
  expect(parseExecution(duplicate)).toBeNull();
  render(<WorkflowGraph workflow={workflow} execution={null} running={false} selected={null} onSelect={vi.fn()} />);
  expect(screen.queryByRole('button', { name: /^Replay$/ })).not.toBeInTheDocument();
  expect(within(screen.getByRole('button', { name: 'Inspect Data Forensics' })).getByText('Timing unavailable')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /RETURNED DISPOSITION/ })).toHaveTextContent('PASS');
});
