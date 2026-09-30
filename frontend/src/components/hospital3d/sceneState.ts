/**
 * Pure event-log -> 3D scene-state reducer (presentation only).
 * Deterministic: identical events always yield identical rooms and slots,
 * which is what the checkpoint tests and the e2e avatar assertions rely on.
 * No clinical logic: rooms mirror the 2D board mapping, statuses mirror
 * recorded actions.
 */
import type { StreamEvent } from '../hospital/api';
import {
  currentDepartment,
  DEPARTMENTS,
  departmentForEvent,
  encounterStatus,
  type Department,
} from '../hospital/departments';

export interface RoomSlot {
  room: Department;
  x: number;
  z: number;
}

export const ROOM_LAYOUT: RoomSlot[] = DEPARTMENTS.map((room, index) => ({
  room,
  x: (index % 4 - 1.5) * 12,
  z: (Math.floor(index / 4) - 0.5) * 11,
}));

export function slotOffset(slot: number): { dx: number; dz: number } {
  if (slot === 0) return { dx: 0, dz: 0 };
  const ring = slot - 1;
  return {
    dx: ((ring % 4) - 1.5) * 1.9,
    dz: Math.floor(ring / 4) % 2 === 0 ? -1.2 : 1.2,
  };
}

export interface AvatarState {
  id: string;
  kind: 'patient' | 'agent';
  label: string;
  room: Department;
  slot: number;
  status: string;
}

export interface SceneSnapshot {
  patients: AvatarState[];
  agents: AvatarState[];
  simTime: number;
}

const AGENT_ACTORS = ['nurse', 'doctor', 'lab', 'radiology', 'pharmacy'] as const;

export function sceneStateAt(events: StreamEvent[], simTime: number = Infinity): SceneSnapshot {
  const cutoff = events.filter((event) => event.sim_time <= simTime);
  const maxTime = cutoff.reduce((max, event) => Math.max(max, event.sim_time), 0);
  const slots = new Map<Department, number>();
  const takeSlot = (room: Department): number => {
    const next = slots.get(room) ?? 0;
    slots.set(room, next + 1);
    return next;
  };

  const byRun = new Map<string, StreamEvent[]>();
  for (const event of cutoff) {
    const list = byRun.get(event.run_id) ?? [];
    list.push(event);
    byRun.set(event.run_id, list);
  }
  const patients: AvatarState[] = [...byRun.entries()]
    .sort(([left], [right]) => (left < right ? -1 : 1))
    .map(([runId, runEvents]) => {
      const room = currentDepartment(runEvents) ?? 'Reception';
      return {
        id: runId,
        kind: 'patient' as const,
        label: runId,
        room,
        slot: takeSlot(room),
        status: encounterStatus(runEvents),
      };
    });

  const agents: AvatarState[] = [];
  for (const actor of AGENT_ACTORS) {
    const mine = cutoff.filter((event) => event.actor === actor);
    if (mine.length === 0) continue;
    const last = mine[mine.length - 1];
    const room = departmentForEvent(actor, last.action);
    agents.push({ id: actor, kind: 'agent' as const, label: actor, room, slot: takeSlot(room), status: '' });
  }

  return { patients, agents, simTime: maxTime };
}
