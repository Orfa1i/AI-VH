import React, { useEffect, useRef } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface FirstPersonControlsProps {
  enabled: boolean;
  onLocationChange?: (locationName: string) => void;
}

export const FirstPersonControls: React.FC<FirstPersonControlsProps> = ({
  enabled,
  onLocationChange,
}) => {
  const { camera, gl } = useThree();
  const keys = useRef<{ [key: string]: boolean }>({});
  const isDragging = useRef(false);
  const prevMouse = useRef({ x: 0, y: 0 });
  const euler = useRef(new THREE.Euler(0, 0, 0, 'YXZ'));
  const currentRoomRef = useRef<string>('');

  // Setup keyboard listeners
  useEffect(() => {
    if (!enabled) return;

    const onKeyDown = (e: KeyboardEvent) => {
      keys.current[e.code] = true;
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
  }, [enabled]);

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

  // Initial position when entering first person / reset on exit
  useEffect(() => {
    if (enabled) {
      // Enter at the West Main Entrance corridor looking East towards Central Nurse Rotunda
      camera.position.set(-13.5, 1.7, 0.0);
      camera.lookAt(0, 1.7, 0);
      euler.current.setFromQuaternion(camera.quaternion);
    } else {
      camera.position.set(0, 24, 20);
      camera.lookAt(0, 0, 0);
    }
  }, [enabled, camera]);

  // Movement update loop
  useFrame((_, delta) => {
    if (!enabled) return;

    const speed = keys.current['ShiftLeft'] || keys.current['ShiftRight'] ? 7.5 : 4.2;
    const moveDist = speed * delta;

    // Movement direction vectors relative to camera view
    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0;
    forward.normalize();

    const right = new THREE.Vector3();
    right.crossVectors(camera.up, forward).negate().normalize();

    if (keys.current['KeyW'] || keys.current['ArrowUp']) {
      camera.position.addScaledVector(forward, moveDist);
    }
    if (keys.current['KeyS'] || keys.current['ArrowDown']) {
      camera.position.addScaledVector(forward, -moveDist);
    }
    if (keys.current['KeyA'] || keys.current['ArrowLeft']) {
      camera.position.addScaledVector(right, -moveDist);
    }
    if (keys.current['KeyD'] || keys.current['ArrowRight']) {
      camera.position.addScaledVector(right, moveDist);
    }

    // Lock eye height at standard standing eye-level (1.7 meters)
    camera.position.y = 1.7;

    // Boundary constraints according to AutoCAD Sheet A-1 building dimensions
    camera.position.x = Math.max(-17.2, Math.min(17.0, camera.position.x));
    camera.position.z = Math.max(-9.8, Math.min(9.8, camera.position.z));

    // Room detection based on AutoCAD blueprint coordinates
    const x = camera.position.x;
    const z = camera.position.z;
    let room = 'Hospital Central Corridor';

    // West Zone (Waiting Area, Reception, Emergency Department)
    if (x <= -8.5) {
      if (z <= -3.8) {
        room = 'Reception & Patient Intake';
      } else if (z <= 3.2) {
        room = 'Patient Waiting Area (Main Lobby)';
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
  });

  return null;
};
