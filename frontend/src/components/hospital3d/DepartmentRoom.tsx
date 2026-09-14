import React from 'react';
import * as THREE from 'three';
import { Html } from '@react-three/drei';

interface DepartmentRoomProps {
  name: string;
  code: string;
  position: [number, number, number];
  size: [number, number, number];
  floorColor: string;
  isActive?: boolean;
  onClick?: () => void;
  iconText?: string;
}

export const DepartmentRoom: React.FC<DepartmentRoomProps> = ({
  name,
  code: _code,
  position,
  size,
  floorColor,
  isActive = false,
  onClick,
  iconText = '🏥',
}) => {
  const [width, _height, depth] = size;
  const wallHeight = 1.2;
  const wallThickness = 0.15;

  return (
    <group position={position} onClick={onClick}>
      {/* Floor Plate */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[width, 0.1, depth]} />
        <meshStandardMaterial
          color={isActive ? '#38bdf8' : floorColor}
          roughness={0.4}
          metalness={0.1}
        />
      </mesh>

      {/* Floor Edge Highlight */}
      <lineSegments position={[0, 0.11, 0]}>
        <edgesGeometry args={[new (THREE as any).BoxGeometry(width, 0.05, depth)]} />
        <lineBasicMaterial color={isActive ? '#38bdf8' : '#334155'} linewidth={2} />
      </lineSegments>

      {/* Back Wall */}
      <mesh position={[0, wallHeight / 2 + 0.1, -depth / 2 + wallThickness / 2]}>
        <boxGeometry args={[width, wallHeight, wallThickness]} />
        <meshStandardMaterial color="#1e293b" roughness={0.7} />
      </mesh>

      {/* Left Wall */}
      <mesh position={[-width / 2 + wallThickness / 2, wallHeight / 2 + 0.1, 0]}>
        <boxGeometry args={[wallThickness, wallHeight, depth]} />
        <meshStandardMaterial color="#1e293b" roughness={0.7} />
      </mesh>

      {/* Right Wall */}
      <mesh position={[width / 2 - wallThickness / 2, wallHeight / 2 + 0.1, 0]}>
        <boxGeometry args={[wallThickness, wallHeight, depth]} />
        <meshStandardMaterial color="#1e293b" roughness={0.7} />
      </mesh>

      {/* Floating Department Sign & Beacon */}
      <Html position={[0, wallHeight + 0.6, 0]} center distanceFactor={15}>
        <div
          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold whitespace-nowrap cursor-pointer transition-all duration-300 shadow-lg flex items-center gap-1.5 ${
            isActive
              ? 'bg-sky-500/90 text-white border-sky-300 shadow-sky-500/50 scale-110 ring-2 ring-sky-400'
              : 'bg-slate-900/80 text-slate-300 border-slate-700 hover:border-slate-500'
          }`}
        >
          <span>{iconText}</span>
          <span>{name}</span>
          {isActive && (
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping ml-1" />
          )}
        </div>
      </Html>
    </group>
  );
};
