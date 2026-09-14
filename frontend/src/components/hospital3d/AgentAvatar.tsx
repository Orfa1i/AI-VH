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
  rotation?: [number, number, number];
}

export const AgentAvatar: React.FC<AgentAvatarProps> = ({
  id: _id,
  name,
  role,
  targetPosition,
  currentAction = 'Standing',
  color: _color,
  rotation = [0, 0, 0],
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const leftLegRef = useRef<THREE.Group>(null);
  const rightLegRef = useRef<THREE.Group>(null);
  const leftArmRef = useRef<THREE.Group>(null);
  const rightArmRef = useRef<THREE.Group>(null);
  const walkCycleRef = useRef<number>(0);

  const targetVec = useRef(new THREE.Vector3(...targetPosition));

  // Update target coordinates
  targetVec.current.set(...targetPosition);

  useFrame((_, delta) => {
    if (groupRef.current) {
      const currentPos = groupRef.current.position;
      const distToTarget = currentPos.distanceTo(targetVec.current);
      const isMoving = distToTarget > 0.08;

      if (isMoving) {
        // Smooth lerp movement towards target department
        currentPos.lerp(targetVec.current, Math.min(delta * 4, 0.25));

        // Rotate character towards movement heading
        const dx = targetVec.current.x - currentPos.x;
        const dz = targetVec.current.z - currentPos.z;
        if (Math.abs(dx) > 0.02 || Math.abs(dz) > 0.02) {
          const moveAngle = Math.atan2(dx, dz);
          groupRef.current.rotation.y = THREE.MathUtils.lerp(
            groupRef.current.rotation.y,
            moveAngle,
            Math.min(delta * 8, 0.3)
          );
        }

        // Advance stride time accumulator
        walkCycleRef.current += delta * 8.5;
        const cycle = walkCycleRef.current;

        // Reciprocal leg stride oscillations around hip joint
        if (leftLegRef.current) {
          leftLegRef.current.rotation.x = Math.sin(cycle) * 0.45;
        }
        if (rightLegRef.current) {
          rightLegRef.current.rotation.x = -Math.sin(cycle) * 0.45;
        }

        // Natural arm counter-swing around shoulder joint
        if (leftArmRef.current) {
          leftArmRef.current.rotation.x = -Math.sin(cycle) * 0.38;
        }
        if (rightArmRef.current) {
          rightArmRef.current.rotation.x = Math.sin(cycle) * 0.38;
        }

        // Vertical step bounce
        currentPos.y = targetPosition[1] + Math.abs(Math.sin(cycle)) * 0.03;
      } else {
        // Smoothly return limbs to idle resting position
        if (leftLegRef.current) {
          leftLegRef.current.rotation.x = THREE.MathUtils.lerp(leftLegRef.current.rotation.x, 0, delta * 8);
        }
        if (rightLegRef.current) {
          rightLegRef.current.rotation.x = THREE.MathUtils.lerp(rightLegRef.current.rotation.x, 0, delta * 8);
        }
        if (leftArmRef.current) {
          leftArmRef.current.rotation.x = THREE.MathUtils.lerp(leftArmRef.current.rotation.x, 0, delta * 8);
        }
        if (rightArmRef.current) {
          rightArmRef.current.rotation.x = THREE.MathUtils.lerp(rightArmRef.current.rotation.x, 0, delta * 8);
        }

        // Gentle breathing idle bob
        currentPos.y = targetPosition[1] + Math.sin(Date.now() * 0.003) * 0.015;

        // Smoothly realign to original station orientation
        groupRef.current.rotation.y = THREE.MathUtils.lerp(
          groupRef.current.rotation.y,
          rotation[1],
          Math.min(delta * 4, 0.15)
        );
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
        return 'bg-sky-600/90 text-sky-100 border-sky-400';
      case 'LAB':
        return 'bg-purple-600/90 text-purple-100 border-purple-400';
      case 'RADIOLOGY':
        return 'bg-indigo-600/90 text-indigo-100 border-indigo-400';
      case 'PHARMACIST':
        return 'bg-teal-600/90 text-teal-100 border-teal-400';
    }
  };

  const isPatient = role === 'PATIENT';
  const skinColor = '#f5c6a5';
  const hairColor = '#382314';

  return (
    <group ref={groupRef} position={targetPosition} rotation={rotation}>
      {/* ── Soft Ground Contact Shadow ── */}
      <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.42, 24]} />
        <meshBasicMaterial color="#000000" opacity={0.32} transparent />
      </mesh>

      {/* ══════════════════════════════════════════════════════════════════
          LOWER BODY: LEGS, PANTS & FEET
          ══════════════════════════════════════════════════════════════════ */}
      {/* Left Leg (Pivots from Hip at y=0.62) */}
      <group ref={leftLegRef} position={[-0.12, 0.62, 0]}>
        {/* Thigh (Patient Scrub Pants / Pajamas) */}
        <mesh position={[0, -0.20, 0]} castShadow>
          <cylinderGeometry args={[0.085, 0.075, 0.38, 16]} />
          <meshStandardMaterial
            color={isPatient ? '#7dd3fc' : role === 'NURSE' ? '#0891b2' : '#334155'}
            roughness={0.5}
          />
        </mesh>

        {/* Lower Leg / Calf */}
        <mesh position={[0, -0.44, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.06, 0.22, 16]} />
          <meshStandardMaterial
            color={isPatient ? skinColor : role === 'NURSE' ? '#0891b2' : '#334155'}
            roughness={0.6}
          />
        </mesh>

        {/* Foot / Footwear */}
        {isPatient ? (
          // Hospital Yellow Fall-Risk Non-Skid Traction Socks
          <group position={[0, -0.565, 0.04]}>
            <mesh castShadow>
              <boxGeometry args={[0.11, 0.08, 0.22]} />
              <meshStandardMaterial color="#facc15" roughness={0.7} />
            </mesh>
            {/* White Rubber Grippers */}
            <mesh position={[0, -0.038, 0]}>
              <boxGeometry args={[0.09, 0.01, 0.18]} />
              <meshStandardMaterial color="#ffffff" roughness={0.3} />
            </mesh>
          </group>
        ) : (
          // Professional Shoes / Clogs
          <mesh position={[0, -0.57, 0.04]} castShadow>
            <boxGeometry args={[0.11, 0.08, 0.22]} />
            <meshStandardMaterial color={role === 'NURSE' ? '#ffffff' : '#0f172a'} roughness={0.3} />
          </mesh>
        )}
      </group>

      {/* Right Leg (Pivots from Hip at y=0.62) */}
      <group ref={rightLegRef} position={[0.12, 0.62, 0]}>
        {/* Thigh */}
        <mesh position={[0, -0.20, 0]} castShadow>
          <cylinderGeometry args={[0.085, 0.075, 0.38, 16]} />
          <meshStandardMaterial
            color={isPatient ? '#7dd3fc' : role === 'NURSE' ? '#0891b2' : '#334155'}
            roughness={0.5}
          />
        </mesh>

        {/* Lower Leg */}
        <mesh position={[0, -0.44, 0]} castShadow>
          <cylinderGeometry args={[0.07, 0.06, 0.22, 16]} />
          <meshStandardMaterial
            color={isPatient ? skinColor : role === 'NURSE' ? '#0891b2' : '#334155'}
            roughness={0.6}
          />
        </mesh>

        {/* Foot */}
        {isPatient ? (
          <group position={[0, -0.565, 0.04]}>
            <mesh castShadow>
              <boxGeometry args={[0.11, 0.08, 0.22]} />
              <meshStandardMaterial color="#facc15" roughness={0.7} />
            </mesh>
            <mesh position={[0, -0.038, 0]}>
              <boxGeometry args={[0.09, 0.01, 0.18]} />
              <meshStandardMaterial color="#ffffff" roughness={0.3} />
            </mesh>
          </group>
        ) : (
          <mesh position={[0, -0.57, 0.04]} castShadow>
            <boxGeometry args={[0.11, 0.08, 0.22]} />
            <meshStandardMaterial color={role === 'NURSE' ? '#ffffff' : '#0f172a'} roughness={0.3} />
          </mesh>
        )}
      </group>


      {/* ══════════════════════════════════════════════════════════════════
          TORSO: PATIENT GOWN / CLINICAL ATTIRE
          ══════════════════════════════════════════════════════════════════ */}
      {/* Lower Torso / Pelvis */}
      <mesh position={[0, 0.68, 0]} castShadow>
        <cylinderGeometry args={[0.22, 0.20, 0.18, 16]} />
        <meshStandardMaterial
          color={isPatient ? '#38bdf8' : role === 'NURSE' ? '#06b6d4' : '#ffffff'}
          roughness={0.4}
        />
      </mesh>

      {/* Main Torso (Patient Gown / Coat) */}
      <mesh position={[0, 0.94, 0]} castShadow>
        <cylinderGeometry args={[0.24, 0.22, 0.38, 16]} />
        <meshStandardMaterial
          color={isPatient ? '#38bdf8' : role === 'NURSE' ? '#06b6d4' : '#ffffff'}
          roughness={0.4}
        />
      </mesh>

      {/* Patient Specific Torso Details */}
      {isPatient && (
        <group>
          {/* White Collar / Neckline Binding */}
          <mesh position={[0, 1.12, 0.13]} rotation={[Math.PI / 2, 0, Math.PI]}>
            <torusGeometry args={[0.12, 0.016, 8, 16, Math.PI]} />
            <meshStandardMaterial color="#ffffff" roughness={0.3} />
          </mesh>

          {/* Patient Hospital Admission ID Label on Chest */}
          <group position={[-0.10, 1.02, 0.22]} rotation={[0, -0.1, 0]}>
            <mesh castShadow>
              <boxGeometry args={[0.08, 0.05, 0.01]} />
              <meshStandardMaterial color="#ffffff" roughness={0.2} />
            </mesh>
            {/* Barcode Strip */}
            <mesh position={[0, -0.008, 0.006]}>
              <boxGeometry args={[0.06, 0.018, 0.002]} />
              <meshStandardMaterial color="#1e293b" />
            </mesh>
          </group>

          {/* Cardiac Telemetry Lead Patch on Right Chest */}
          <mesh position={[0.10, 1.04, 0.22]} rotation={[0, 0.1, 0]}>
            <circleGeometry args={[0.024, 16]} />
            <meshStandardMaterial color="#22c55e" roughness={0.3} />
          </mesh>
        </group>
      )}

      {/* Doctor Stethoscope */}
      {role === 'DOCTOR' && (
        <group position={[0, 1.0, 0.12]}>
          <mesh>
            <torusGeometry args={[0.15, 0.022, 8, 16, Math.PI]} />
            <meshStandardMaterial color="#334155" metalness={0.8} />
          </mesh>
          <mesh position={[0, -0.14, 0.02]}>
            <cylinderGeometry args={[0.025, 0.025, 0.015, 12]} />
            <meshStandardMaterial color="#94a3b8" metalness={0.9} roughness={0.2} />
          </mesh>
        </group>
      )}

      {/* ══════════════════════════════════════════════════════════════════
          ARMS, SLEEVES & HANDS
          ══════════════════════════════════════════════════════════════════ */}
      {/* Left Arm (Pivots from Shoulder at y=1.04) */}
      <group ref={leftArmRef} position={[-0.26, 1.04, 0]}>
        {/* Upper Arm Sleeve */}
        <mesh position={[-0.04, -0.11, 0]} rotation={[0, 0, 0.18]} castShadow>
          <cylinderGeometry args={[0.075, 0.085, 0.24, 16]} />
          <meshStandardMaterial
            color={isPatient ? '#38bdf8' : role === 'NURSE' ? '#06b6d4' : '#ffffff'}
            roughness={0.4}
          />
        </mesh>

        {/* Forearm */}
        <mesh position={[-0.08, -0.32, 0.02]} rotation={[0.08, 0, 0.12]} castShadow>
          <cylinderGeometry args={[0.055, 0.048, 0.22, 16]} />
          <meshStandardMaterial color={skinColor} roughness={0.6} />
        </mesh>

        {/* Hand */}
        <mesh position={[-0.10, -0.47, 0.03]} castShadow>
          <sphereGeometry args={[0.055, 12, 12]} />
          <meshStandardMaterial color={skinColor} roughness={0.6} />
        </mesh>

        {/* Patient IV Port / Cannula Dressing on Left Hand */}
        {isPatient && (
          <group position={[-0.10, -0.46, 0.08]} rotation={[0.2, 0, 0]}>
            {/* Transparent Tegaderm Adhesive Dressing */}
            <mesh>
              <boxGeometry args={[0.042, 0.042, 0.008]} />
              <meshStandardMaterial color="#93c5fd" transparent opacity={0.65} roughness={0.1} />
            </mesh>
            {/* IV Cannula Hub */}
            <mesh position={[0, 0, 0.008]} rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[0.008, 0.008, 0.024, 8]} />
              <meshStandardMaterial color="#3b82f6" metalness={0.5} />
            </mesh>
          </group>
        )}
      </group>

      {/* Right Arm (Pivots from Shoulder at y=1.04) */}
      <group ref={rightArmRef} position={[0.26, 1.04, 0]}>
        {/* Upper Arm Sleeve */}
        <mesh position={[0.04, -0.11, 0]} rotation={[0, 0, -0.18]} castShadow>
          <cylinderGeometry args={[0.075, 0.085, 0.24, 16]} />
          <meshStandardMaterial
            color={isPatient ? '#38bdf8' : role === 'NURSE' ? '#06b6d4' : '#ffffff'}
            roughness={0.4}
          />
        </mesh>


        {/* Forearm */}
        <mesh position={[0.08, -0.32, 0.02]} rotation={[0.08, 0, -0.12]} castShadow>
          <cylinderGeometry args={[0.055, 0.048, 0.22, 16]} />
          <meshStandardMaterial color={skinColor} roughness={0.6} />
        </mesh>

        {/* Patient Hospital Admission Barcode Wristband on Right Wrist */}
        {isPatient && (
          <group position={[0.08, -0.38, 0.02]}>
            {/* White Band */}
            <mesh rotation={[0, 0, 0.12]}>
              <cylinderGeometry args={[0.058, 0.058, 0.04, 16]} />
              <meshStandardMaterial color="#ffffff" roughness={0.3} />
            </mesh>
            {/* Red Identification Stripe */}
            <mesh position={[0, 0, 0.002]} rotation={[0, 0, 0.12]}>
              <cylinderGeometry args={[0.059, 0.059, 0.012, 16]} />
              <meshStandardMaterial color="#ef4444" roughness={0.3} />
            </mesh>
          </group>
        )}

        {/* Hand */}
        <mesh position={[0.10, -0.47, 0.03]} castShadow>
          <sphereGeometry args={[0.055, 12, 12]} />
          <meshStandardMaterial color={skinColor} roughness={0.6} />
        </mesh>
      </group>

      {/* ══════════════════════════════════════════════════════════════════
          NECK & HEAD
          ══════════════════════════════════════════════════════════════════ */}
      {/* Neck */}
      <mesh position={[0, 1.18, 0]} castShadow>
        <cylinderGeometry args={[0.085, 0.095, 0.14, 16]} />
        <meshStandardMaterial color={skinColor} roughness={0.6} />
      </mesh>

      {/* Head Cranium */}
      <mesh position={[0, 1.40, 0]} castShadow>
        <sphereGeometry args={[0.19, 20, 20]} />
        <meshStandardMaterial color={skinColor} roughness={0.6} />
      </mesh>

      {/* ── Hair (Cropped Male Haircut) ── */}
      <group position={[0, 1.40, 0]}>
        {/* Main Hair Volume */}
        <mesh position={[0, 0.04, -0.01]} castShadow>
          <sphereGeometry args={[0.195, 20, 20, 0, Math.PI * 2, 0, Math.PI * 0.52]} />
          <meshStandardMaterial color={hairColor} roughness={0.8} />
        </mesh>
        {/* Hair Fringe / Front Hairline */}
        <mesh position={[0, 0.14, 0.12]} rotation={[-0.25, 0, 0]}>
          <boxGeometry args={[0.17, 0.04, 0.06]} />
          <meshStandardMaterial color={hairColor} roughness={0.8} />
        </mesh>
        {/* Left Sideburn */}
        <mesh position={[-0.185, 0.03, 0.04]}>
          <boxGeometry args={[0.02, 0.09, 0.04]} />
          <meshStandardMaterial color={hairColor} roughness={0.8} />
        </mesh>
        {/* Right Sideburn */}
        <mesh position={[0.185, 0.03, 0.04]}>
          <boxGeometry args={[0.02, 0.09, 0.04]} />
          <meshStandardMaterial color={hairColor} roughness={0.8} />
        </mesh>
      </group>

      {/* ── Ears ── */}
      {/* Left Ear */}
      <mesh position={[-0.195, 1.39, 0]} scale={[0.5, 1.1, 0.8]}>
        <sphereGeometry args={[0.035, 8, 8]} />
        <meshStandardMaterial color={skinColor} roughness={0.6} />
      </mesh>
      {/* Right Ear */}
      <mesh position={[0.195, 1.39, 0]} scale={[0.5, 1.1, 0.8]}>
        <sphereGeometry args={[0.035, 8, 8]} />
        <meshStandardMaterial color={skinColor} roughness={0.6} />
      </mesh>

      {/* ══════════════════════════════════════════════════════════════════
          FACIAL FEATURES: EYES, EYEBROWS, NOSE, MOUTH
          ══════════════════════════════════════════════════════════════════ */}
      <group position={[0, 1.40, 0.16]}>
        {/* ── Left Eye ── */}
        <group position={[-0.065, 0.045, 0]}>
          {/* Sclera (White) */}
          <mesh>
            <sphereGeometry args={[0.032, 12, 12]} />
            <meshStandardMaterial color="#ffffff" roughness={0.2} />
          </mesh>
          {/* Pupil & Iris (Deep Dark Brown) */}
          <mesh position={[0, 0, 0.024]}>
            <sphereGeometry args={[0.018, 12, 12]} />
            <meshStandardMaterial color="#1e293b" roughness={0.1} />
          </mesh>
          {/* Catchlight / Sparkle */}
          <mesh position={[0.007, 0.007, 0.034]}>
            <sphereGeometry args={[0.006, 8, 8]} />
            <meshBasicMaterial color="#ffffff" />
          </mesh>
        </group>

        {/* ── Right Eye ── */}
        <group position={[0.065, 0.045, 0]}>
          {/* Sclera (White) */}
          <mesh>
            <sphereGeometry args={[0.032, 12, 12]} />
            <meshStandardMaterial color="#ffffff" roughness={0.2} />
          </mesh>
          {/* Pupil & Iris */}
          <mesh position={[0, 0, 0.024]}>
            <sphereGeometry args={[0.018, 12, 12]} />
            <meshStandardMaterial color="#1e293b" roughness={0.1} />
          </mesh>
          {/* Catchlight */}
          <mesh position={[0.007, 0.007, 0.034]}>
            <sphereGeometry args={[0.006, 8, 8]} />
            <meshBasicMaterial color="#ffffff" />
          </mesh>
        </group>

        {/* ── Eyebrows ── */}
        {/* Left Eyebrow */}
        <mesh position={[-0.068, 0.098, 0.006]} rotation={[0, 0, 0.08]}>
          <boxGeometry args={[0.065, 0.016, 0.02]} />
          <meshStandardMaterial color={hairColor} roughness={0.8} />
        </mesh>
        {/* Right Eyebrow */}
        <mesh position={[0.068, 0.098, 0.006]} rotation={[0, 0, -0.08]}>
          <boxGeometry args={[0.065, 0.016, 0.02]} />
          <meshStandardMaterial color={hairColor} roughness={0.8} />
        </mesh>

        {/* ── 3D Nose ── */}
        <mesh position={[0, -0.015, 0.024]} rotation={[Math.PI / 8, 0, 0]} castShadow>
          <coneGeometry args={[0.026, 0.075, 4]} />
          <meshStandardMaterial color="#e5a985" roughness={0.6} />
        </mesh>

        {/* ── Mouth & Lips ── */}
        <mesh position={[0, -0.088, 0.01]}>
          <boxGeometry args={[0.062, 0.016, 0.018]} />
          <meshStandardMaterial color="#be6b7b" roughness={0.5} />
        </mesh>
      </group>

      {/* ══════════════════════════════════════════════════════════════════
          FLOATING NAME & STATUS BADGE
          ══════════════════════════════════════════════════════════════════ */}
      <Html position={[0, 1.88, 0]} center distanceFactor={14} zIndexRange={[10, 0]}>
        <div className="flex flex-col items-center pointer-events-none select-none">
          <div
            className={`px-2.5 py-0.5 rounded-full border text-[11px] font-bold shadow-md uppercase tracking-wider ${getRoleBadgeStyle()}`}
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

export default AgentAvatar;
