/** Pure presentation mapping: recorded actor/action -> board department. */

export const DEPARTMENTS = [
  'ER',
  'Reception',
  'Lab',
  'Radiology',
  'Pharmacy',
  'Wards',
  'ICU',
  'Clinics',
] as const;

export type Department = (typeof DEPARTMENTS)[number];

export function departmentForEvent(actor: string, action: string): Department {
  const text = `${actor} ${action}`.toLowerCase();
  if (text.includes('lab')) return 'Lab';
  if (text.includes('imag') || text.includes('radiolog')) return 'Radiology';
  if (text.includes('medicat') || text.includes('pharmac')) return 'Pharmacy';
  if (text.includes('consult') || text.includes('clinic')) return 'Clinics';
  if (text.includes('vital') || text.includes('triage') || text.includes('observ')) return 'ER';
  if (text.includes('diagnos') || text.includes('submit_report') || text.includes('assess')) return 'Wards';
  return 'Reception';
}

export function currentDepartment(
  events: Array<{ actor: string; action: string }>,
): Department | null {
  if (events.length === 0) return null;
  const last = events[events.length - 1];
  return departmentForEvent(last.actor, last.action);
}

export function encounterStatus(events: Array<{ action: string }>): string {
  if (events.length === 0) return 'Pending';
  const last = events[events.length - 1].action;
  if (last === 'submit_report') return 'Report filed';
  return 'In care';
}
