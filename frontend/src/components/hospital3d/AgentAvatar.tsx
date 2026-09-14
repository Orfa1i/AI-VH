import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface AgentAvatarProps {
  id: string;
  name: string;
  role: 'DOCTOR' | 'NURSE' | 'PATIENT' | 'LAB' | 'RADIOLOGY' | 'PHARMACIST';
  targetPosition: [number, number, number];
  currentAction?: string;
  color: string;
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({
  id: _id,
  name,
  role,
  targetPosition,
  currentAction = 'Standing',
  color,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const targetVec = useRef(new THREE.Vector3(...targetPosition));

  // Update target coordinates
  targetVec.current.set(...targetPosition);

  useFrame((_, delta) => {
    if (groupRef.current) {
      // Smooth lerp movement towards target department
      groupRef.current.position.lerp(targetVec.current, Math.min(delta * 4, 0.2));
      
      // Slight gentle breathing bounce when stationary
      const isMoving = groupRef.current.position.distanceTo(targetVec.current) > 0.1;
      if (!isMoving) {
        groupRef.current.position.y = targetPosition[1] + Math.sin(Date.now() * 0.003) * 0.04;
      }
    }
  });

  const getRoleBadgeStyle = () => {
    switch (role) {
      case 'DOCTOR':
        return 'bg-emerald-600/90 text-emerald-100 border-emerald-400';
      case 'NURSE':
        return 'bg-cyan-600/90 text-cyan-100 border-cyan-400';
      case 'PATIENT':
        return 'bg-amber-600/90 text-amber-100 border-amber-400';
      case 'LAB':
        return 'bg-purple-600/90 text-purple-100 border-purple-400';
      case 'RADIOLOGY':
        return 'bg-indigo-600/90 text-indigo-100 border-indigo-400';
      case 'PHARMACIST':
        return 'bg-teal-600/90 text-teal-100 border-teal-400';
    }
  };

  return (
    <group ref={groupRef} position={targetPosition}>
      {/* Soft Ground Shadow Disc */}
      <mesh position={[0, 0.08, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.4, 16]} />
        <meshBasicMaterial color="#000000" opacity={0.3} transparent />
      </mesh>

      {/* Torso / Clinical Coat */}
      <mesh position={[0, 0.75, 0]} castShadow>
        <cylinderGeometry args={[0.22, 0.28, 0.7, 16]} />
        <meshStandardMaterial color={color} roughness={0.3} />
      </mesh>

      {/* Head */}
      <mesh position={[0, 1.3, 0]} castShadow>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshStandardMaterial color="#fcd34d" roughness={0.6} />
      </mesh>

      {/* Doctor Stethoscope / Accessory */}
      {role === 'DOCTOR' && (
        <mesh position={[0, 0.95, 0.12]}>
          <torusGeometry args={[0.15, 0.03, 8, 16, Math.PI]} />
          <meshStandardMaterial color="#64748b" metalness={0.8} />
        </mesh>
      )}

      {/* Floating Name & Status Badge */}
      <Html position={[0, 1.75, 0]} center distanceFactor={14} zIndexRange={[10, 0]}>
        <div className="flex flex-col items-center pointer-events-none">
          <div
            className={`px-2 py-0.5 rounded-full border text-[11px] font-bold shadow-md uppercase tracking-wider ${getRoleBadgeStyle()}`}
          >
            {role}: {name}
          </div>
          {currentAction && (
            <div className="mt-0.5 px-2 py-0.5 rounded bg-slate-900/80 text-[10px] text-slate-300 border border-slate-700 whitespace-nowrap shadow">
              {currentAction}
            </div>
          )}
        </div>
      </Html>
    </group>
  );
};
