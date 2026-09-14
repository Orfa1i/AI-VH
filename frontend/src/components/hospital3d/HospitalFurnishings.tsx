import React from 'react';

/**
 * 3D Clinical Furnishings
 * Adds examination beds, desks, computer workstations, IV poles, lab analyzer benches,
 * and a CT scanner gantry so the first-person walkthrough feels authentic and immersive.
 */

export const HospitalFurnishings: React.FC = () => {
  return (
    <group>
      {/* --- RECEPTION DESK --- */}
      <group position={[-8, 0, -5]}>
        {/* Counter Desk */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <boxGeometry args={[3.2, 1.1, 0.8]} />
          <meshStandardMaterial color="#334155" roughness={0.3} />
        </mesh>
        {/* Computer Screen */}
        <mesh position={[0.5, 1.3, -0.1]}>
          <boxGeometry args={[0.7, 0.45, 0.05]} />
          <meshStandardMaterial color="#0f172a" roughness={0.2} />
        </mesh>
        {/* Screen Display Glow */}
        <mesh position={[0.5, 1.3, -0.07]}>
          <planeGeometry args={[0.65, 0.4]} />
          <meshBasicMaterial color="#38bdf8" />
        </mesh>
      </group>

      {/* --- NURSE TRIAGE DESK & VITALS CART --- */}
      <group position={[6, 0, -5]}>
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <boxGeometry args={[3.8, 1.1, 0.8]} />
          <meshStandardMaterial color="#0f766e" roughness={0.4} />
        </mesh>
        {/* Dual Workstation Monitors */}
        <mesh position={[-0.8, 1.3, -0.1]}>
          <boxGeometry args={[0.7, 0.45, 0.05]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[0.8, 1.3, -0.1]}>
          <boxGeometry args={[0.7, 0.45, 0.05]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        {/* Vitals Monitor Pole */}
        <mesh position={[-2.2, 0.8, 0]}>
          <cylinderGeometry args={[0.04, 0.04, 1.6]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.8} />
        </mesh>
        {/* Monitor Screen on Pole */}
        <mesh position={[-2.2, 1.5, 0.1]}>
          <boxGeometry args={[0.45, 0.35, 0.1]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[-2.2, 1.5, 0.16]}>
          <planeGeometry args={[0.4, 0.3]} />
          <meshBasicMaterial color="#10b981" />
        </mesh>
      </group>

      {/* --- EXAMINATION ROOM 1: CLINICAL BED & IV POLE --- */}
      <group position={[-7, 0, 1]}>
        {/* Bed Frame */}
        <mesh position={[0, 0.3, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.5, 0.4, 2.6]} />
          <meshStandardMaterial color="#475569" roughness={0.5} />
        </mesh>
        {/* Mattress */}
        <mesh position={[0, 0.58, 0]}>
          <boxGeometry args={[1.4, 0.22, 2.5]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.6} />
        </mesh>
        {/* Pillow */}
        <mesh position={[0, 0.72, -0.9]}>
          <boxGeometry args={[1.0, 0.12, 0.5]} />
          <meshStandardMaterial color="#cbd5e1" roughness={0.8} />
        </mesh>
        {/* Bed Rails */}
        <mesh position={[-0.72, 0.7, 0]}>
          <boxGeometry args={[0.04, 0.35, 1.8]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.7} />
        </mesh>
        <mesh position={[0.72, 0.7, 0]}>
          <boxGeometry args={[0.04, 0.35, 1.8]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.7} />
        </mesh>
        {/* IV Drip Pole */}
        <mesh position={[-1.2, 1.1, -0.8]}>
          <cylinderGeometry args={[0.03, 0.03, 2.2]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.8} />
        </mesh>
        {/* IV Bag */}
        <mesh position={[-1.2, 1.95, -0.65]}>
          <boxGeometry args={[0.18, 0.3, 0.08]} />
          <meshStandardMaterial color="#e0f2fe" opacity={0.8} transparent />
        </mesh>
      </group>

      {/* --- EXAMINATION ROOM 2: SECOND CLINICAL BED --- */}
      <group position={[-0.5, 0, 1]}>
        <mesh position={[0, 0.3, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.5, 0.4, 2.6]} />
          <meshStandardMaterial color="#475569" roughness={0.5} />
        </mesh>
        <mesh position={[0, 0.58, 0]}>
          <boxGeometry args={[1.4, 0.22, 2.5]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.6} />
        </mesh>
        <mesh position={[0, 0.72, -0.9]}>
          <boxGeometry args={[1.0, 0.12, 0.5]} />
          <meshStandardMaterial color="#cbd5e1" />
        </mesh>
      </group>

      {/* --- DOCTOR STATION: PHYSICIAN DESK & CHAIR --- */}
      <group position={[6.5, 0, 1]}>
        {/* Doctor Desk */}
        <mesh position={[0, 0.5, 0]} castShadow receiveShadow>
          <boxGeometry args={[2.8, 0.95, 1.2]} />
          <meshStandardMaterial color="#1e293b" roughness={0.3} />
        </mesh>
        {/* Dual Diagnostic Displays */}
        <mesh position={[-0.5, 1.25, -0.2]}>
          <boxGeometry args={[0.8, 0.5, 0.05]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[-0.5, 1.25, -0.17]}>
          <planeGeometry args={[0.75, 0.45]} />
          <meshBasicMaterial color="#38bdf8" />
        </mesh>
        <mesh position={[0.5, 1.25, -0.2]}>
          <boxGeometry args={[0.8, 0.5, 0.05]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[0.5, 1.25, -0.17]}>
          <planeGeometry args={[0.75, 0.45]} />
          <meshBasicMaterial color="#10b981" />
        </mesh>
      </group>

      {/* --- CLINICAL LABORATORY: ANALYZER BENCHES --- */}
      <group position={[-7, 0, 8]}>
        {/* Heavy Lab Workbench */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <boxGeometry args={[4.2, 1.05, 1.1]} />
          <meshStandardMaterial color="#1e1b4b" roughness={0.3} />
        </mesh>
        {/* Automated Hematology / Chemistry Analyzer */}
        <mesh position={[-1.2, 1.35, 0]}>
          <boxGeometry args={[1.2, 0.6, 0.7]} />
          <meshStandardMaterial color="#e2e8f0" metalness={0.3} roughness={0.4} />
        </mesh>
        {/* Centrifuge Unit */}
        <mesh position={[1.2, 1.25, 0]}>
          <cylinderGeometry args={[0.4, 0.4, 0.4, 16]} />
          <meshStandardMaterial color="#64748b" metalness={0.7} />
        </mesh>
      </group>

      {/* --- RADIOLOGY: CT SCANNER GANTRY RING & TABLE --- */}
      <group position={[-0.5, 0, 8]}>
        {/* Scanner Gantry Ring */}
        <mesh position={[0, 1.4, -0.8]} rotation={[0, 0, 0]}>
          <torusGeometry args={[1.1, 0.35, 16, 32]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.2} metalness={0.1} />
        </mesh>
        {/* Patient Scan Table */}
        <mesh position={[0, 0.5, 0.4]} castShadow receiveShadow>
          <boxGeometry args={[1.0, 0.4, 2.2]} />
          <meshStandardMaterial color="#64748b" metalness={0.6} />
        </mesh>
        <mesh position={[0, 0.72, 0.4]}>
          <boxGeometry args={[0.9, 0.08, 2.1]} />
          <meshStandardMaterial color="#38bdf8" />
        </mesh>
      </group>
    </group>
  );
};
