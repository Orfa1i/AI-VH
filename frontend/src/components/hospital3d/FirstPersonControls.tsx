import React, { useEffect, useRef } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export interface ProximityTarget {
  id: string;
  name: string;
  actionPrompt: string;
  station: string;
  x: number;
  z: number;
  radius: number;
}

export const INTERACTION_STATIONS: ProximityTarget[] = [
  {
    id: 'INTERNAL_MEDICINE',
    name: 'Dr. Marcus Vance, MD (Internal Medicine)',
    actionPrompt: 'Consult Specialist Physician',
    station: 'Doctor Station (Physician Office)',
    x: 2.6,
    z: -6.8,
    radius: 3.5,
  },
  {
    id: 'PHARMACY',
    name: 'Dr. Elena Rostova, PharmD (Clinical Pharmacist)',
    actionPrompt: 'Review Prescriptions & Dispensing',
    station: 'Hospital Pharmacy',
    x: 8.4,
    z: 0.5,
    radius: 3.5,
  },
  {
    id: 'LABORATORY',
    name: 'David Chen, MLS (Clinical Laboratory)',
    actionPrompt: 'Inspect Biomarker Analyzers',
    station: 'Clinical Pathology Laboratory',
    x: 7.8,
    z: -6.8,
    radius: 3.5,
  },
  {
    id: 'RADIOLOGY',
    name: 'Dr. Hayes, MD (Radiology Imaging Suite)',
    actionPrompt: 'Inspect CT Gantry & Scans',
    station: 'Radiology CT Suite',
    x: 7.8,
    z: 6.8,
    radius: 3.5,
  },
  {
    id: 'NURSE_STATION',
    name: 'Sarah Jenkins, RN (Rotunda Triage Desk)',
    actionPrompt: 'Run Simulated Patient Encounter',
    station: 'Central Rotunda Nurse Station',
    x: -0.8,
    z: 0.0,
    radius: 3.5,
  },
];

interface FirstPersonControlsProps {
  enabled: boolean;
  onLocationChange?: (locationName: string) => void;
  onProximityChange?: (target: ProximityTarget | null) => void;
  onInteract?: (stationId: string) => void;
}

export const FirstPersonControls: React.FC<FirstPersonControlsProps> = ({
  enabled,
  onLocationChange,
  onProximityChange,
  onInteract,
}) => {
  const { camera, gl } = useThree();
  const keys = useRef<{ [key: string]: boolean }>({});
  const isDragging = useRef(false);
  const prevMouse = useRef({ x: 0, y: 0 });
  const euler = useRef(new THREE.Euler(0, 0, 0, 'YXZ'));
  const currentRoomRef = useRef<string>('');
  const currentProximityRef = useRef<ProximityTarget | null>(null);

  // Setup keyboard listeners
  useEffect(() => {
    if (!enabled) return;

    const onKeyDown = (e: KeyboardEvent) => {
      keys.current[e.code] = true;
      if ((e.code === 'KeyE' || e.key === 'e' || e.key === 'E') && currentProximityRef.current) {
        if (onInteract) {
          onInteract(currentProximityRef.current.id);
        }
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      keys.current[e.code] = false;
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);

    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, [enabled, onInteract]);

  // Setup mouse look via pointer drag
  useEffect(() => {
    if (!enabled) return;
    const dom = gl.domElement;

    const onPointerDown = (e: PointerEvent) => {
      isDragging.current = true;
      prevMouse.current = { x: e.clientX, y: e.clientY };
    };

    const onPointerMove = (e: PointerEvent) => {
      if (!isDragging.current) return;
      const deltaX = e.clientX - prevMouse.current.x;
      const deltaY = e.clientY - prevMouse.current.y;
      prevMouse.current = { x: e.clientX, y: e.clientY };

      euler.current.setFromQuaternion(camera.quaternion);
      euler.current.y -= deltaX * 0.0035;
      euler.current.x -= deltaY * 0.0035;
      // Clamp vertical pitch to look up/down without flipping
      euler.current.x = Math.max(-Math.PI / 2.3, Math.min(Math.PI / 2.3, euler.current.x));
      camera.quaternion.setFromEuler(euler.current);
    };

    const onPointerUp = () => {
      isDragging.current = false;
    };

    dom.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);

    return () => {
      dom.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [enabled, camera, gl]);

  // Initialize camera position in reception lobby when first person is toggled
  useEffect(() => {
    if (enabled) {
      camera.position.set(-11.5, 1.4, 0);
      euler.current.set(0, -Math.PI / 2, 0);
      camera.quaternion.setFromEuler(euler.current);
    }
  }, [enabled, camera]);

  useFrame((_, delta) => {
    if (!enabled) return;

    // Walking speed (sprint with Shift)
    const baseSpeed = keys.current['ShiftLeft'] || keys.current['ShiftRight'] ? 5.5 : 3.2;
    const moveSpeed = baseSpeed * delta;

    // Movement direction vectors relative to current camera heading
    const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
    forward.y = 0;
    forward.normalize();

    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
    right.y = 0;
    right.normalize();

    const moveVector = new THREE.Vector3();

    if (keys.current['KeyW'] || keys.current['ArrowUp']) moveVector.add(forward);
    if (keys.current['KeyS'] || keys.current['ArrowDown']) moveVector.sub(forward);
    if (keys.current['KeyD'] || keys.current['ArrowRight']) moveVector.add(right);
    if (keys.current['KeyA'] || keys.current['ArrowLeft']) moveVector.sub(right);

    if (moveVector.lengthSq() > 0) {
      moveVector.normalize().multiplyScalar(moveSpeed);
      camera.position.add(moveVector);
    }

    // Keep camera at realistic eye level
    camera.position.y = 1.4;

    // Building boundaries matching Sheet A-1 footprint
    camera.position.x = Math.max(-17.2, Math.min(17.0, camera.position.x));
    camera.position.z = Math.max(-9.8, Math.min(9.8, camera.position.z));

    const x = camera.position.x;
    const z = camera.position.z;

    // Determine room based on exact AutoCAD architectural coordinates
    let room = 'Hospital Central Corridor';

    // West Wing Rooms
    if (x <= -6.0) {
      if (z <= -1.8) {
        room = 'Reception & Patient Waiting Area';
      } else if (z <= 1.8) {
        room = 'Main Hospital Entrance Vestibule';
      } else {
        room = 'Emergency Department (Acute Bays & Triage)';
      }
    }
    // East Inpatient Wing (4 Patient Rooms)
    else if (x >= 11.5) {
      if (z <= -4.8) {
        room = 'Inpatient Patient Room 1';
      } else if (z <= 0) {
        room = 'Inpatient Patient Room 2';
      } else if (z <= 4.8) {
        room = 'Inpatient Patient Room 3';
      } else {
        room = 'Inpatient Patient Room 4';
      }
    }
    // North Wing Rooms
    else if (z < -4.0) {
      if (x <= -3.0) {
        room = 'Examination Room 1';
      } else if (x <= 0.5) {
        room = 'Examination Room 2';
      } else if (x <= 5.0) {
        room = 'Doctor Station (Physician Office)';
      } else {
        room = 'Clinical Laboratory';
      }
    }
    // South Wing Rooms
    else if (z > 4.0) {
      if (x <= -2.8) {
        room = 'Examination Room 3';
      } else if (x <= 0.0) {
        room = 'Examination Room 4';
      } else if (x <= 2.8) {
        room = 'Examination Room 5';
      } else if (x <= 5.8) {
        room = 'Examination Room 6';
      } else {
        room = 'Radiology (CT & X-Ray Suite)';
      }
    }
    // Central Hub & Inner Block
    else {
      const distToNurseStation = Math.sqrt((x - (-0.8)) ** 2 + z ** 2);
      if (distToNurseStation <= 2.5) {
        room = 'Central Rotunda Nurse Station';
      } else if (x >= 2.0 && x <= 6.2) {
        room = 'Doctor Station (Consultation Suite)';
      } else if (x > 6.2 && x < 11.5) {
        room = 'Pharmacy (Dispensing & Medication Store)';
      } else {
        room = 'Hospital Central Corridor';
      }
    }

    if (room !== currentRoomRef.current) {
      currentRoomRef.current = room;
      if (onLocationChange) onLocationChange(room);
    }

    // Proximity calculation for interactive stations
    let closestStation: ProximityTarget | null = null;
    let minDistance = Infinity;

    for (const station of INTERACTION_STATIONS) {
      const dist = Math.sqrt((x - station.x) ** 2 + (z - station.z) ** 2);
      if (dist <= station.radius && dist < minDistance) {
        minDistance = dist;
        closestStation = station;
      }
    }

    if (closestStation?.id !== currentProximityRef.current?.id) {
      currentProximityRef.current = closestStation;
      if (onProximityChange) onProximityChange(closestStation);
    }
  });

  return null;
};
