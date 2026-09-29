import { isRecord, strings } from '../../api/investigation';
import { humanize, measurement } from './presentation';

export function EvidenceList({ title, value }: { title: string; value: unknown }) {
  const items = strings(value);
  return <section className="evidence-section"><h3>{title}</h3>{items.length
    ? <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul>
    : <p className="not-provided">{Array.isArray(value) && value.length === 0 ? 'None reported.' : 'Not provided in the response.'}</p>}</section>;
}

/** Readable nested fields for guardrails, validation locations, and metadata. */
export function FieldValue({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (value === null || value === undefined) return <span className="not-provided">Not provided</span>;
  if (typeof value === 'boolean') return <span>{value ? 'Yes' : 'No'}</span>;
  if (typeof value === 'number') return <span>{Number.isFinite(value) ? String(value) : measurement(value)}</span>;
  if (typeof value === 'string') return <span>{['Infinity', '-Infinity', 'NaN'].includes(value) ? measurement(value) : value}</span>;
  if (depth > 3) return <span className="not-provided">See raw output for nested detail.</span>;
  if (Array.isArray(value)) return value.length ? <ul className="field-list">{value.map((item, index) => <li key={index}><FieldValue value={item} depth={depth + 1} /></li>)}</ul> : <span className="not-provided">None reported</span>;
  if (isRecord(value)) return <dl className="field-record">{Object.entries(value).map(([key, item]) => <div key={key}><dt>{humanize(key)}</dt><dd><FieldValue value={item} depth={depth + 1} /></dd></div>)}</dl>;
  return <span className="not-provided">Unrecognized value</span>;
}

export function Narrative({ title, value }: { title: string; value: unknown }) {
  return <section className="evidence-section"><h3>{title}</h3><FieldValue value={value} /></section>;
}
