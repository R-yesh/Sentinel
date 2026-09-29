import { AGENT_IDS, type AgentId, type WorkflowState } from '../../api/investigation';

export const AGENTS: Record<AgentId, { name: string; description: string; kind: string }> = {
  data_forensics: { name: 'Data Forensics', description: 'Validate component & peer observations', kind: 'VALIDATION' },
  drift_intelligence: { name: 'Drift Intelligence', description: 'Early drift & 168h forecast', kind: 'TEMPORAL ANALYSIS' },
  lot_intelligence: { name: 'Lot Intelligence', description: 'Robust statistics & Isolation Forest', kind: 'PEER ANALYSIS' },
  latent_defect: { name: 'Latent Defect', description: 'Synthesize corroborating evidence', kind: 'EVIDENCE SYNTHESIS' },
  adversarial_qa: { name: 'Adversarial QA', description: 'Challenge the provisional assessment', kind: 'STRUCTURED REASONING' },
  reliability_judge: { name: 'Reliability Judge', description: 'Adjudicate the reliability disposition', kind: 'DECISION' },
  explanation: { name: 'Explanation', description: 'Document evidence & recommended action', kind: 'ENGINEERING EXPLANATION' },
};
export const STAGES: AgentId[][] = [['data_forensics'], ['drift_intelligence', 'lot_intelligence'], ['latent_defect'], ['adversarial_qa'], ['reliability_judge'], ['explanation']];
export const hasEvidence = (workflow: WorkflowState, id: AgentId) => workflow.agent_outputs[id] !== undefined || workflow.findings.some((finding) => finding.agent === id);
export const contributedAgents = (workflow: WorkflowState) => AGENT_IDS.filter((id) => hasEvidence(workflow, id));
export const needsAttention = (workflow: WorkflowState, id: AgentId) => workflow.findings.some((finding) => finding.agent === id && ['medium', 'high', 'critical'].includes(finding.severity ?? ''));
export const humanize = (value: string) => value.replaceAll('_', ' ').toLowerCase().replace(/^./, (character) => character.toUpperCase());

export function measurement(value: unknown, digits = 4): string {
  if (typeof value === 'number' && Number.isFinite(value)) return value.toFixed(digits);
  if (value === 'Infinity') return '+∞';
  if (value === '-Infinity') return '−∞';
  if (value === 'NaN') return 'NaN (not a number)';
  return 'Not provided';
}

export interface FieldSpec { key: string; label: string; unit?: string; digits?: number; percentile?: boolean }
export const METRICS: Partial<Record<AgentId, FieldSpec[]>> = {
  drift_intelligence: [
    { key: 'percentage_change', label: 'Observed early change', unit: '%' },
    { key: 'early_slope', label: 'Observed early slope', unit: 'µA/h' },
    { key: 'predicted_168h', label: 'Model forecast · 168h', unit: 'µA' },
    { key: 'prediction_uncertainty', label: 'Model tree disagreement', unit: 'µA' },
  ],
  lot_intelligence: [
    { key: 'lot_population_size', label: 'Peer population', digits: 0 },
    { key: 'lot_median', label: 'Lot median · 24h', unit: 'µA' },
    { key: 'lot_mad', label: 'Lot MAD', unit: 'µA' },
    { key: 'robust_z_score', label: 'Robust z-score' },
    { key: 'percentile', label: 'Percentile rank', unit: '%', percentile: true },
    { key: 'robust_anomaly_score', label: 'Robust anomaly measure' },
    { key: 'isolation_score', label: 'Isolation Forest score' },
  ],
};
