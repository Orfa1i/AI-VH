import { describe, expect, it } from 'vitest';
import type { StreamEvent } from '../../hospital/api';
import { ROOM_LAYOUT, sceneStateAt, slotOffset } from '../sceneState';

function evt(overrides: Partial<StreamEvent> & { event_id: string }): StreamEvent {
  return {
    run_id: 'run-1',
    sim_time: 0,
    wall_time: '2026-09-30T00:00:00+00:00',
    actor: 'doctor',
    action: 'order_lab',
    payload: {},
    result_ref: null,
    ...overrides,
  };
}

describe('sceneStateAt', () => {
  it('maps an empty log to empty rooms', () => {
    const snapshot = sceneStateAt([]);
    expect(snapshot.patients).toEqual([]);
    expect(snapshot.agents).toEqual([]);
    expect(snapshot.simTime).toBe(0);
  });

  it('places patient avatars in the room of their latest event', () => {
    const events = [
      evt({ event_id: 'e1', run_id: 'run-1', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
      evt({ event_id: 'e2', run_id: 'run-1', actor: 'doctor', action: 'order_lab', sim_time: 5 }),
    ];
    const snapshot = sceneStateAt(events);
    expect(snapshot.patients).toHaveLength(1);
    expect(snapshot.patients[0]).toMatchObject({ id: 'run-1', kind: 'patient', room: 'Lab' });
  });

  it('matches the event log at checkpoints', () => {
    const events = [
      evt({ event_id: 'e1', run_id: 'run-1', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
      evt({ event_id: 'e2', run_id: 'run-1', actor: 'doctor', action: 'order_lab', sim_time: 5 }),
      evt({ event_id: 'e3', run_id: 'run-1', actor: 'doctor', action: 'submit_report', sim_time: 45 }),
    ];
    expect(sceneStateAt(events, 0).patients[0].room).toBe('ER');
    expect(sceneStateAt(events, 15).patients[0].room).toBe('Lab');
    expect(sceneStateAt(events, 45).patients[0].room).toBe('Wards');
    expect(sceneStateAt(events, 45).patients[0].status).toBe('Report filed');
  });

  it('tracks agent avatars by their latest action department', () => {
    const events = [
      evt({ event_id: 'e1', run_id: 'run-1', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
      evt({ event_id: 'e2', run_id: 'run-1', actor: 'doctor', action: 'order_lab', sim_time: 5 }),
      evt({ event_id: 'e3', run_id: 'run-2', actor: 'pharmacy', action: 'request_medication_info', sim_time: 6 }),
    ];
    const snapshot = sceneStateAt(events);
    const rooms = Object.fromEntries(snapshot.agents.map((a) => [a.id, a.room]));
    expect(rooms).toMatchObject({ nurse: 'ER', doctor: 'Lab', pharmacy: 'Pharmacy' });
    expect(snapshot.agents.every((a) => a.kind === 'agent')).toBe(true);
  });

  it('assigns deterministic slots and room centers', () => {
    expect(ROOM_LAYOUT).toHaveLength(8);
    const first = ROOM_LAYOUT[0];
    expect(first.room).toBe('ER');
    expect(slotOffset(0)).toEqual({ dx: 0, dz: 0 });
    expect(slotOffset(1)).not.toEqual(slotOffset(2));
    const snapshot = sceneStateAt([
      evt({ event_id: 'e1', run_id: 'run-b', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
      evt({ event_id: 'e2', run_id: 'run-a', actor: 'nurse', action: 'request_vitals', sim_time: 0 }),
    ]);
    // Deterministic run order regardless of event arrival order.
    expect(snapshot.patients.map((p) => p.id)).toEqual(['run-a', 'run-b']);
    expect(snapshot.patients[0].slot).toBe(0);
    expect(snapshot.patients[1].slot).toBe(1);
  });
});
