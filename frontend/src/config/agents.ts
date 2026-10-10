// src/config/agents.ts
// Canonical shared configuration for Virtual Hospital clinical specialist agents.

export type AgentKey = 'im' | 'ca' | 'ne' | 'su' | 'em' | 'ob' | 'gy';

export interface AgentConfig {
  name: string;
  short: string;
  color: string;
  book: string;
}

export const AGENTS: Record<AgentKey, AgentConfig> = {
  im: { name: 'Internal Medicine', short: 'Internal Med.', color: '#2B2FD9', book: "Harrison's Principles of Internal Medicine" },
  ca: { name: 'Cardiology', short: 'Cardiology', color: '#1F7BEA', book: "Braunwald's Heart Disease" },
  ne: { name: 'Neurology', short: 'Neurology', color: '#5B3DF5', book: "Adams and Victor's Principles of Neurology" },
  su: { name: 'Surgery', short: 'Surgery', color: '#13A06B', book: "Schwartz's Principles of Surgery" },
  em: { name: 'Emergency Medicine', short: 'Emergency', color: '#0E9AA7', book: "Tintinalli's Emergency Medicine" },
  ob: { name: 'Obstetrics', short: 'Obstetrics', color: '#2E9FE6', book: 'Williams Obstetrics' },
  gy: { name: 'Gynecology', short: 'Gynecology', color: '#0FA88A', book: 'Williams Gynecology' },
};

export type RouteStatus = 'lead' | 'assigned' | 'standby';

export interface RoutingResult {
  routedAt: string; // ISO time
  scores: Record<AgentKey, number>; // 0–100, from MedGemma
  status: Record<AgentKey, RouteStatus>; // exactly one 'lead'
}

// Demo values for the preeclampsia case until the live router is wired:
export const DEMO_ROUTING: RoutingResult = {
  routedAt: '2026-10-09T14:17:00',
  scores: { ob: 97, em: 92, im: 88, ca: 81, ne: 79, su: 64, gy: 18 },
  status: { ob: 'lead', em: 'assigned', im: 'assigned', ca: 'assigned', ne: 'assigned', su: 'assigned', gy: 'standby' },
};
