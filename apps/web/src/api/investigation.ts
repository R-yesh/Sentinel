import { parseExecution, type WorkflowExecution } from './execution';

export const AGENT_IDS = ['data_forensics', 'drift_intelligence', 'lot_intelligence', 'latent_defect', 'adversarial_qa', 'reliability_judge', 'explanation'] as const;
export type AgentId = typeof AGENT_IDS[number];
export type Decision = 'PASS' | 'REVIEW' | 'REJECT';
export type WorkflowStatus = 'pending' | 'running' | 'needs_review' | 'completed' | 'failed';
export type Fields = Record<string, unknown>;
export interface InvestigationSelection { dataset_id: string; component_id: string }
export interface Finding {
  agent: string;
  component_id: string;
  finding_type: string;
  severity: string | null;
  summary: string;
  evidence: string[];
  metadata: Fields;
}
export interface WorkflowState {
  workflow_id: string;
  component_id: string;
  lot_id: string | null;
  status: WorkflowStatus;
  raw_data: Fields;
  lot_context: Fields | null;
  findings: Finding[];
  agent_outputs: Partial<Record<AgentId, Fields>> & Record<string, Fields | undefined>;
  final_decision: Decision | null;
  explanation: string | null;
}
export interface InvestigationResult {
  dataset_id: string;
  workflow_execution?: WorkflowExecution | null;
  workflow: WorkflowState;
  /** Transport completeness notes, never analytical findings. */
  issues: string[];
  raw: unknown;
}
export const isRecord = (value: unknown): value is Fields => typeof value === 'object' && value !== null && !Array.isArray(value);
export const text = (value: unknown): string | null => typeof value === 'string' && value.trim() ? value : null;
export const strings = (value: unknown): string[] => Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];

/** Validate the envelope; tolerate missing evidence without inventing defaults. */
export function parseInvestigation(value: unknown, selection: InvestigationSelection): InvestigationResult {
  if (!isRecord(value) || !isRecord(value.workflow)) throw new Error('Invalid investigation response: workflow is missing.');
  const w = value.workflow;
  if (value.dataset_id !== selection.dataset_id || w.component_id !== selection.component_id || !text(w.workflow_id)) {
    throw new Error('Investigation response identity does not match the selected component.');
  }
  const statuses: string[] = ['pending', 'running', 'needs_review', 'completed', 'failed'];
  if (typeof w.status !== 'string' || !statuses.includes(w.status)) throw new Error('Investigation response has an unrecognized workflow status.');
  const issues: string[] = [];
  if (w.status === 'pending' || w.status === 'running') issues.push('The response is not a finished workflow. No live progress connection exists.');
  const objectField = (field: string): Fields => {
    if (isRecord(w[field])) return w[field];
    issues.push(`${field} was missing or malformed.`);
    return {};
  };
  const outputs: WorkflowState['agent_outputs'] = {};
  for (const [agent, output] of Object.entries(objectField('agent_outputs'))) {
    if (isRecord(output)) outputs[agent] = output;
    else issues.push(`${agent} output was malformed; see raw response.`);
  }
  const findings: Finding[] = [];
  if (!Array.isArray(w.findings)) issues.push('Findings were missing or malformed.');
  else for (const item of w.findings) {
    if (!isRecord(item) || !text(item.agent) || !text(item.finding_type) || !text(item.summary)) {
      issues.push('An unreadable finding was omitted from the presentation; see raw response.');
      continue;
    }
    if (!Array.isArray(item.evidence) || item.evidence.some((entry) => typeof entry !== 'string') || !isRecord(item.metadata)) {
      issues.push('A finding has incomplete evidence or metadata; see raw response.');
    }
    findings.push({
      agent: item.agent as string, component_id: text(item.component_id) ?? selection.component_id,
      finding_type: item.finding_type as string, summary: item.summary as string,
      severity: text(item.severity), evidence: strings(item.evidence), metadata: isRecord(item.metadata) ? item.metadata : {},
    });
  }
  const decisions: unknown[] = ['PASS', 'REVIEW', 'REJECT'];
  const decision = decisions.includes(w.final_decision) ? w.final_decision as Decision : null;
  if (w.final_decision != null && !decision) issues.push('The final decision is unrecognized. It has not been inferred from other fields.');
  if (w.status === 'completed' && !decision) issues.push('The workflow is marked completed but contains no recognized final decision.');
  if (outputs.reliability_judge?.decision && outputs.reliability_judge.decision !== decision) issues.push('Judge output and final_decision differ. The disposition below preserves final_decision.');
  const rawData = objectField('raw_data');
  const execution = parseExecution(value.workflow_execution);
  if (value.workflow_execution != null && !execution) issues.push('Execution telemetry was malformed; timing replay is unavailable. Analytical evidence is preserved.');
  return {
    workflow_execution: execution,
    dataset_id: selection.dataset_id, raw: value, issues: [...new Set(issues)],
    workflow: {
      workflow_id: w.workflow_id as string, component_id: selection.component_id,
      lot_id: text(w.lot_id), status: w.status as WorkflowStatus,
      raw_data: rawData, lot_context: isRecord(w.lot_context) ? w.lot_context : null,
      findings, agent_outputs: outputs, final_decision: decision, explanation: text(w.explanation),
    },
  };
}
