import type { ScreeningComponent } from './population';

export interface Coverage { total: number; evaluated: number; excluded: number; flagged: number; not_flagged: number; flag_rate: number | null }
export interface EvaluationComponent {
  early: ScreeningComponent;
  hindsight: { defect_type: string | null; synthetic_class: 'healthy' | 'defective' | 'unknown'; leakage_96h: number | null; leakage_168h: number | null };
  evaluated: boolean;
  comparison_bucket: 'sentinel_only' | 'conventional_only' | 'both' | 'neither' | null;
}
export interface EvaluationResponse {
  dataset_id: string; evaluation_only: true; snapshot_id: string; screening_method: string;
  healthy_label: string; defective_labels: string[];
  summary: { total: number; evaluated: number; excluded: number; unknown_labels: number; candidates: number; screening_rate: number | null; healthy: Coverage; defective: Coverage };
  by_defect_type: (Coverage & { defect_type: string })[];
  signal_overlap: { drift_only: number; lot_only: number; both: number; neither: number };
  comparison: { status: 'configured' | 'unconfigured'; limit_ua: number | null; rule: string; comparable_defective: number; excluded_defective: number; conventional_flagged: number | null; sentinel_flagged: number | null; conventional_only: number | null; sentinel_only: number | null; both: number | null; neither: number | null };
  components: EvaluationComponent[];
}
export const percent = (value: number | null) => value === null ? 'Unavailable' : `${value.toFixed(1)}%`;
