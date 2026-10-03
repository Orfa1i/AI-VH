import React, { memo, useEffect, useMemo, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import type { StreamEvent } from '../hospital/api';
import { DEPARTMENTS, type Department } from '../hospital/departments';
import { ROOM_LAYOUT, sceneStateAt, slotOffset, type AvatarState } from './sceneState';

declare global {
  interface Window {
    __board3d?: {
      fps: number;
      loadMs: number;
      avatarRooms: () => Record<string, string>;
      avatarScreenPos: (id: string) => { x: number; y: number } | null;
    };
  }
}

const ROOM_COLORS: Record<Department, string> = {
  ER: '#e0f2fe',
  Reception: '#f1f5f8',
  Lab: '#ede9fe',
  Radiology: '#e0e7ff',
  Pharmacy: '#dcfce7',
  Wards: '#fef9c3',
  ICU: '#ffe4e6',
  Clinics: '#ffedd5',
};

interface Registry {
  camera: THREE.Camera | null;
  size: { width: number; height: number };
  rect: { left: number; top: number; width: number; height: number } | null;
  objects: Map<string, THREE.Object3D>;
}

const registry: Registry = {
  camera: null,
  size: { width: 800, height: 450 },
  rect: null,
  objects: new Map(),
};

function SceneRig({ onFrame }: { onFrame: (fps: number) => void }) {
  const { camera, gl, size } = useThree();
  const frames = React.useRef(0);
  const last = React.useRef(0);
  const ema = React.useRef(60);
  React.useEffect(() => {
    registry.camera = camera;
    const rect = gl.domElement.getBoundingClientRect();
    registry.rect = { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
    registry.size = { width: size.width, height: size.height };
  });
  useFrame(() => {
    registry.camera = camera;
    frames.current += 1;
    const now = performance.now();
    if (last.current === 0) last.current = now;
    if (frames.current >= 30) {
      const instant = (frames.current * 1000) / Math.max(1, now - last.current);
      last.current = now;
      frames.current = 0;
      ema.current = ema.current * 0.5 + instant * 0.5;
      onFrame(Math.round(ema.current));
    }
  });
  return null;
}

function Room({ room, x, z }: { room: Department; x: number; z: number }) {
  return (
    <group position={[x, 0, z]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[10, 8]} />
        <meshLambertMaterial color={ROOM_COLORS[room]} />
      </mesh>
      <mesh position={[0, 0.6, -4]}>
        <boxGeometry args={[10, 1.2, 0.3]} />
        <meshLambertMaterial color="#cbd5e1" />
      </mesh>
      <mesh position={[-5, 0.6, 0]}>
        <boxGeometry args={[0.3, 1.2, 8]} />
        <meshLambertMaterial color="#cbd5e1" />
      </mesh>
    </group>
  );
}

function PatientAvatar({
  avatar,
  x,
  z,
  selected,
  onSelect,
}: {
  avatar: AvatarState;
  x: number;
  z: number;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const target = useMemo(() => new THREE.Vector3(x, 0.55, z), [x, z]);
  useEffect(() => {
    const mesh = ref.current;
    if (mesh !== null) registry.objects.set(avatar.id, mesh);
    return () => {
      registry.objects.delete(avatar.id);
    };
  }, [avatar.id]);
  useFrame((_, delta) => {
    const mesh = ref.current;
    if (mesh === null) return;
    mesh.position.lerp(target, 1 - Math.exp(-6 * delta));
  });
  const color = avatar.status === 'Report filed' ? '#16a34a' : '#0284c7';
  return (
    <group>
      <mesh
        ref={ref}
        position={[x, 0.55, z]}
        onClick={(event) => {
          event.stopPropagation();
          onSelect(avatar.id);
        }}
      >
        <sphereGeometry args={[0.55, 20, 14]} />
        <meshLambertMaterial color={selected ? '#ffffff' : color} />
      </mesh>
      {selected && (
        <mesh position={[x, 0.06, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.8, 1.0, 32]} />
          <meshBasicMaterial color="#0284c7" side={THREE.DoubleSide} />
        </mesh>
      )}
    </group>
  );
}

function AgentAvatar({ avatar, x, z }: { avatar: AvatarState; x: number; z: number }) {
  const ref = useRef<THREE.Mesh>(null);
  const target = useMemo(() => new THREE.Vector3(x, 0.4, z), [x, z]);
  useEffect(() => {
    const mesh = ref.current;
    if (mesh !== null) registry.objects.set(`agent:${avatar.id}`, mesh);
    return () => {
      registry.objects.delete(`agent:${avatar.id}`);
    };
  }, [avatar.id]);
  useFrame((_, delta) => {
    const mesh = ref.current;
    if (mesh === null) return;
    mesh.position.lerp(target, 1 - Math.exp(-6 * delta));
    mesh.rotation.y += delta * 0.8;
  });
  return (
    <mesh ref={ref} position={[x, 0.4, z]}>
      <octahedronGeometry args={[0.4]} />
      <meshLambertMaterial color="#d97706" />
    </mesh>
  );
}

interface Scene3DProps {
  events: StreamEvent[];
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
  onReady: (loadMs: number) => void;
}

export const Scene3D: React.FC<Scene3DProps> = memo(
  function Scene3D({ events, selectedRunId, onSelectRun, onReady }) {
  const mountTimeRef = useRef<number>(performance.now());
  const snapshot = useMemo(() => sceneStateAt(events), [events]);
  const fpsRef = useRef(0);
  const readyRef = useRef(false);

  useEffect(() => {
    window.__board3d = {
      fps: 0,
      loadMs: -1,
      avatarRooms: () => Object.fromEntries(snapshot.patients.map((p) => [p.id, p.room])),
      avatarScreenPos: (id: string) => {
        const object = registry.objects.get(id);
        const { camera, rect } = registry;
        if (object === undefined || object === null || camera === null || rect === null) return null;
        const point = new THREE.Vector3();
        object.getWorldPosition(point);
        point.project(camera);
        if (point.z > 1) return null;
        return {
          x: rect.left + ((point.x * 0.5 + 0.5) * rect.width),
          y: rect.top + ((-point.y * 0.5 + 0.5) * rect.height),
        };
      },
    };
  }, [snapshot]);

  const roomCenter = new Map(ROOM_LAYOUT.map((entry) => [entry.room, entry] as const));
  const place = (room: Department, slot: number): [number, number] => {
    const center = roomCenter.get(room) ?? { x: 0, z: 0 };
    const offset = slotOffset(slot);
    return [center.x + offset.dx, center.z + offset.dz];
  };

  return (
    <Canvas
      dpr={0.75}
      gl={{ antialias: false, powerPreference: 'low-power' }}
      camera={{ position: [0, 24, 19], fov: 45 }}
      onCreated={() => {
        if (!readyRef.current) {
          readyRef.current = true;
          const loadMs = performance.now() - mountTimeRef.current;
          fpsRef.current = 0;
          if (window.__board3d !== undefined) window.__board3d.loadMs = Math.round(loadMs);
          onReady(loadMs);
        }
      }}
    >
      <color attach="background" args={['#f8fafc']} />
      <ambientLight intensity={0.9} />
      <directionalLight position={[8, 14, 6]} intensity={0.9} />
      <SceneRig
        onFrame={(fps) => {
          fpsRef.current = fps;
          if (window.__board3d !== undefined) window.__board3d.fps = fps;
        }}
      />
      {ROOM_LAYOUT.map((entry) => (
        <Room key={entry.room} room={entry.room} x={entry.x} z={entry.z} />
      ))}
      {snapshot.patients.map((avatar) => {
        const [x, z] = place(avatar.room, avatar.slot);
        return (
          <PatientAvatar
            key={avatar.id}
            avatar={avatar}
            x={x}
            z={z}
            selected={avatar.id === selectedRunId}
            onSelect={onSelectRun}
          />
        );
      })}
      {snapshot.agents.map((avatar) => {
        const [x, z] = place(avatar.room, avatar.slot);
        return <AgentAvatar key={`agent:${avatar.id}`} avatar={avatar} x={x} z={z} />;
      })}
    </Canvas>
  );
},
// Shallow prop check: stable events reference + stable callbacks (see section)
// keep shell clock ticks from reconciling the canvas tree.
(prev, next) =>
  prev.events === next.events &&
  prev.selectedRunId === next.selectedRunId &&
  prev.onSelectRun === next.onSelectRun &&
  prev.onReady === next.onReady,
);

export { DEPARTMENTS };
