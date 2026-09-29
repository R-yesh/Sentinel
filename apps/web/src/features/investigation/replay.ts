import { useEffect, useMemo, useState } from 'react';
import type { WorkflowExecution } from '../../api/execution';

/** One monotone time map for every branch: event order and overlap are preserved.
 * Stretch short intervals, compress long ones, then cap total replay at six seconds.
 * This presentation clock is never displayed as a measured execution duration. */
export function replayTimeline(execution?: WorkflowExecution | null) {
  if (!execution) return null;
  const times = [...new Set([0, execution.total_duration_ms, ...execution.agents.flatMap((a) => a.status === 'not_executed' ? [] : [a.start_offset_ms!, a.end_offset_ms!])])].sort((a, b) => a - b);
  const mapped = [0];
  for (let i = 1; i < times.length; i++) mapped.push(mapped[i - 1] + Math.min(700, Math.max(100, times[i] - times[i - 1])));
  const end = mapped.at(-1)!;
  const scale = Math.min(1, 6000 / (end || 1));
  const at = (time: number) => mapped[times.indexOf(time)] * scale;
  return { duration: end * scale, agents: execution.agents.map((a) => ({ ...a, start: a.start_offset_ms === null ? null : at(a.start_offset_ms), end: a.end_offset_ms === null ? null : at(a.end_offset_ms) })) };
}

export function useExecutionReplay(execution?: WorkflowExecution | null) {
  const timeline = useMemo(() => replayTimeline(execution), [execution]);
  const [cursor, setCursor] = useState(Infinity);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    const animate = !!timeline?.duration && !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    setCursor(animate ? 0 : Infinity); setPlaying(animate);
  }, [timeline]);
  useEffect(() => {
    if (!playing || !timeline) return;
    let previous = performance.now();
    const timer = window.setInterval(() => {
      const now = performance.now(); const delta = now - previous; previous = now;
      setCursor((value) => Math.min(timeline.duration, value + delta));
    }, 30);
    return () => window.clearInterval(timer);
  }, [playing, timeline]);
  useEffect(() => { if (playing && timeline && cursor >= timeline.duration) setPlaying(false); }, [cursor, timeline, playing]);
  return { timeline, cursor, playing, complete: !timeline || cursor >= timeline.duration,
    replay: () => { setCursor(0); setPlaying(true); },
    toggle: () => setPlaying((v) => !v),
    reset: () => { setCursor(0); setPlaying(false); },
    skip: () => { setCursor(Infinity); setPlaying(false); } };
}
