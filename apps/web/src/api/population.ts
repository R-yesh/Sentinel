import type { ComponentObservation } from './client';

export interface ScreeningComponent extends ComponentObservation {
  percentage_change: number | null;
  early_slope: number | null;
  lot_evidence: string | null;
  robust_z_score: number | string | null;
  candidate: boolean | null;
  reasons: string[];
  issue: string | null;
  conventional_flag: boolean | null;
}
export interface LotSummary { lot_id: string; total: number; screened: number; candidates: number; unassessed: number }
export interface PopulationResponse {
  dataset_id: string;
  snapshot_id: string;
  method: string;
  early_drift_threshold_percent: number;
  summary: { total: number; lots: number; screened: number; unassessed: number; candidates: number; no_screening_signal: number; significant_drift: number; high_side_lot: number };
  comparison: { status: 'configured' | 'unconfigured'; limit_ua: number | null; rule: string; comparable: number; excluded: number; conventional_only: number | null; sentinel_only: number | null; both: number | null; neither: number | null };
  lots: LotSummary[];
  drift_histogram: { lower: number; upper: number; count: number }[];
  components: ScreeningComponent[];
}
