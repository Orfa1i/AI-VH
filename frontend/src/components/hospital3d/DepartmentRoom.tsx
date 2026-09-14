import React from 'react';
import * as THREE from 'three';
import { Html } from '@react-three/drei';

interface DepartmentRoomProps {
  name: string;
  code: string;
  position: [number, number, number];
  size: [number, number, number];
  floorColor?: string;
  wallColor?: string;
  isActive?: boolean;
  onClick?: () => void;
  iconText?: string;
  doorSide?: 'north' | 'south' | 'east' | 'west' | 'open';
}

export const DepartmentRoom: React.FC<DepartmentRoomProps> = ({
  name,
  code: _code,
  position,
  size,
  floorColor = '#f8fafc',
  wallColor = '#ffffff',
  isActive = false,
  onClick,
  iconText = '🏥',
  doorSide = 'south',
}) => {
  const [width, _height, depth] = size;
  const wallHeight = 1.35;
  const wallThickness = 0.12;
  const doorWidth = 1.4;

  return (
    <group position={position} onClick={onClick}>
      {/* Porcelain Tile Floor Plate */}
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[width, 0.1, depth]} />
        <meshStandardMaterial
          color={isActive ? '#e0f2fe' : floorColor}
          roughness={0.25}
          metalness={0.05}
        />
      </mesh>

      {/* Clean Ceramic Edge Bevel Highlight */}
      <lineSegments position={[0, 0.105, 0]}>
        <edgesGeometry args={[new (THREE as any).BoxGeometry(width, 0.01, depth)]} />
        <lineBasicMaterial color={isActive ? '#0284c7' : '#cbd5e1'} linewidth={1.5} />
      </lineSegments>

      {/* Back Wall (North Wall) */}
      {doorSide !== 'north' ? (
        <mesh position={[0, wallHeight / 2 + 0.1, -depth / 2 + wallThickness / 2]}>
          <boxGeometry args={[width, wallHeight, wallThickness]} />
          <meshStandardMaterial color={wallColor} roughness={0.3} />
        </mesh>
      ) : (
        /* Wall with Doorway Opening */
        <group position={[0, 0, -depth / 2 + wallThickness / 2]}>
          <mesh position={[-(width - (width - doorWidth) / 2) / 2 - doorWidth / 4, wallHeight / 2 + 0.1, 0]}>
            <boxGeometry args={[(width - doorWidth) / 2, wallHeight, wallThickness]} />
            <meshStandardMaterial color={wallColor} roughness={0.3} />
          </mesh>
          <mesh position={[(width - (width - doorWidth) / 2) / 2 + doorWidth / 4, wallHeight / 2 + 0.1, 0]}>
            <boxGeometry args={[(width - doorWidth) / 2, wallHeight, wallThickness]} />
            <meshStandardMaterial color={wallColor} roughness={0.3} />
          </mesh>
        </group>
      )}

      {/* Left Wall (West Wall) */}
      {doorSide !== 'west' ? (
        <mesh position={[-width / 2 + wallThickness / 2, wallHeight / 2 + 0.1, 0]}>
          <boxGeometry args={[wallThickness, wallHeight, depth]} />
          <meshStandardMaterial color={wallColor} roughness={0.3} />
        </mesh>
      ) : null}

      {/* Right Wall (East Wall) */}
      {doorSide !== 'east' ? (
        <mesh position={[width / 2 - wallThickness / 2, wallHeight / 2 + 0.1, 0]}>
          <boxGeometry args={[wallThickness, wallHeight, depth]} />
          <meshStandardMaterial color={wallColor} roughness={0.3} />
        </mesh>
      ) : null}

      {/* Front Wall (South Wall) */}
      {doorSide === 'south' ? (
        /* Wall with Doorway Opening */
        <group position={[0, 0, depth / 2 - wallThickness / 2]}>
          <mesh position={[-(width - doorWidth) / 4 - doorWidth / 2, wallHeight / 2 + 0.1, 0]}>
            <boxGeometry args={[(width - doorWidth) / 2, wallHeight, wallThickness]} />
            <meshStandardMaterial color={wallColor} roughness={0.3} />
          </mesh>
          <mesh position={[(width - doorWidth) / 4 + doorWidth / 2, wallHeight / 2 + 0.1, 0]}>
            <boxGeometry args={[(width - doorWidth) / 2, wallHeight, wallThickness]} />
            <meshStandardMaterial color={wallColor} roughness={0.3} />
          </mesh>
        </group>
      ) : doorSide !== 'open' ? (
        <mesh position={[0, wallHeight / 2 + 0.1, depth / 2 - wallThickness / 2]}>
          <boxGeometry args={[width, wallHeight, wallThickness]} />
          <meshStandardMaterial color={wallColor} roughness={0.3} />
        </mesh>
      ) : null}

      {/* Medical Accent Trim (Cyan Chair-Rail Band) */}
      <mesh position={[0, 0.75, -depth / 2 + wallThickness / 2 + 0.01]}>
        <boxGeometry args={[width - 0.05, 0.08, 0.01]} />
        <meshStandardMaterial color="#38bdf8" roughness={0.2} />
      </mesh>

      {/* Floating Modern Clinical Sign */}
      <Html position={[0, wallHeight + 0.6, 0]} center distanceFactor={16} zIndexRange={[10, 0]}>
        <div
          className={`px-3 py-1.5 rounded-xl border text-xs font-bold whitespace-nowrap cursor-pointer transition-all duration-300 shadow-md flex items-center gap-1.5 ${
            isActive
              ? 'bg-sky-500 text-white border-sky-300 shadow-sky-500/30 scale-105 ring-2 ring-sky-300'
              : 'bg-white/95 text-slate-800 border-slate-200 hover:border-sky-400 hover:text-sky-700 shadow-slate-200/50'
          }`}
        >
          <span className="text-sm">{iconText}</span>
          <span>{name}</span>
          {isActive && (
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping ml-1" />
          )}
        </div>
      </Html>
    </group>
  );
};
