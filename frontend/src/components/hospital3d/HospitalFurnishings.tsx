import React from 'react';

/**
 * 3D Architectural Clinical Furnishings (AutoCAD Floor Plan Sheet A-1)
 * Faithfully models every zone in the blueprint:
 * - Reception & Patient Waiting Area
 * - Emergency Department (7 Acute bays + Triage Desk + Ambulance Entry)
 * - Central Circular Rotunda Nurse Station
 * - 6 Examination Rooms (2 North, 4 South)
 * - 2 Doctor Stations (North Physician Office & Central Consultation Suite)
 * - Clinical Laboratory with Central Double-Sided Island
 * - Pharmacy with Dispensing Counter & Medication Shelving
 * - Radiology CT Scanner Suite with Operator Console & Ensuite
 * - 4 Inpatient Patient Rooms with Private Ensuites
 */

export const HospitalFurnishings: React.FC = () => {
  return (
    <group>
      {/* ═══════════════════════════════════════════════════════════════
          ZONE 1: RECEPTION & WAITING AREA (WEST)
          ═══════════════════════════════════════════════════════════════ */}
      {/* Curved Reception Desk */}
      <group position={[-12.5, 0, -6.5]}>
        {/* Curved front counter */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[2.6, 2.6, 1.1, 24, 1, false, Math.PI * 0.2, Math.PI * 0.8]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} metalness={0.05} side={2} />
        </mesh>
        {/* Reception counter top trim (Cyan) */}
        <mesh position={[0, 1.12, 0]}>
          <cylinderGeometry args={[2.7, 2.7, 0.06, 24, 1, false, Math.PI * 0.18, Math.PI * 0.84]} />
          <meshStandardMaterial color="#38bdf8" roughness={0.1} side={2} />
        </mesh>
        {/* Staff computers */}
        <mesh position={[-0.8, 1.35, -0.4]}>
          <boxGeometry args={[0.55, 0.38, 0.04]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[0.6, 1.35, -0.3]}>
          <boxGeometry args={[0.55, 0.38, 0.04]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
      </group>

      {/* Waiting Area Seating (West Wall: 5 Chairs) */}
      <group position={[-16.8, 0, -1]}>
        {[-1.6, -0.8, 0, 0.8, 1.6].map((zOffset, i) => (
          <group key={i} position={[0, 0, zOffset]}>
            {/* Seat Cushion (Medical Blue) */}
            <mesh position={[0, 0.45, 0]} castShadow>
              <boxGeometry args={[0.55, 0.12, 0.55]} />
              <meshStandardMaterial color="#0284c7" roughness={0.5} />
            </mesh>
            {/* Backrest */}
            <mesh position={[-0.22, 0.72, 0]}>
              <boxGeometry args={[0.1, 0.45, 0.52]} />
              <meshStandardMaterial color="#0369a1" roughness={0.5} />
            </mesh>
            {/* Chrome legs */}
            <mesh position={[0, 0.22, 0]}>
              <cylinderGeometry args={[0.02, 0.02, 0.44]} />
              <meshStandardMaterial color="#cbd5e1" metalness={0.8} />
            </mesh>
          </group>
        ))}
      </group>

      {/* Waiting Area Seating (South Row: 8 Chairs) */}
      <group position={[-12.5, 0, 2.2]}>
        {[-2.8, -2.0, -1.2, -0.4, 0.4, 1.2, 2.0, 2.8].map((xOffset, i) => (
          <group key={i} position={[xOffset, 0, 0]}>
            <mesh position={[0, 0.45, 0]} castShadow>
              <boxGeometry args={[0.55, 0.12, 0.55]} />
              <meshStandardMaterial color="#0284c7" roughness={0.5} />
            </mesh>
            <mesh position={[0, 0.72, 0.22]}>
              <boxGeometry args={[0.52, 0.45, 0.1]} />
              <meshStandardMaterial color="#0369a1" roughness={0.5} />
            </mesh>
          </group>
        ))}
      </group>

      {/* ═══════════════════════════════════════════════════════════════
          ZONE 2: EMERGENCY DEPARTMENT (ED) (SOUTHWEST)
          ═══════════════════════════════════════════════════════════════ */}
      {/* ED Stretcher Bays (North Row: 3 Bays) */}
      {[-15.2, -13.2, -11.2].map((xPos, idx) => (
        <group key={`ed-n-${idx}`} position={[xPos, 0, 4.4]}>
          {/* Stretcher Bed */}
          <mesh position={[0, 0.4, 0]} castShadow receiveShadow>
            <boxGeometry args={[1.0, 0.25, 2.1]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.3} />
          </mesh>
          {/* Stretcher Frame (Medical Stainless Steel) */}
          <mesh position={[0, 0.2, 0]}>
            <boxGeometry args={[1.05, 0.15, 2.15]} />
            <meshStandardMaterial color="#94a3b8" metalness={0.7} />
          </mesh>
          {/* Privacy Curtain Divider Rail */}
          <mesh position={[0.6, 1.6, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.02, 0.02, 2.2]} />
            <meshStandardMaterial color="#cbd5e1" metalness={0.8} />
          </mesh>
        </group>
      ))}

      {/* ED Stretcher Bays (South Row: 3 Bays) */}
      {[-15.2, -13.2, -11.2].map((xPos, idx) => (
        <group key={`ed-s-${idx}`} position={[xPos, 0, 8.8]}>
          <mesh position={[0, 0.4, 0]} castShadow receiveShadow>
            <boxGeometry args={[1.0, 0.25, 2.1]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.3} />
          </mesh>
          <mesh position={[0, 0.2, 0]}>
            <boxGeometry args={[1.05, 0.15, 2.15]} />
            <meshStandardMaterial color="#94a3b8" metalness={0.7} />
          </mesh>
        </group>
      ))}

      {/* Triage Desk & Ambulance Entrance Dock */}
      <group position={[-8.5, 0, 6.8]}>
        {/* Triage Workstation Counter */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.8, 1.1, 0.8]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} />
        </mesh>
        <mesh position={[0, 1.12, 0]}>
          <boxGeometry args={[1.85, 0.05, 0.85]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        {/* Vitals Telemetry Monitor */}
        <mesh position={[0.4, 1.35, 0]}>
          <boxGeometry args={[0.4, 0.35, 0.08]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[0.4, 1.35, 0.05]}>
          <planeGeometry args={[0.35, 0.3]} />
          <meshBasicMaterial color="#10b981" />
        </mesh>
      </group>

      {/* Ambulance Entrance Marker (Yellow Floor Arrow) */}
      <group position={[-8.5, 0.02, 10.2]}>
        <mesh receiveShadow>
          <planeGeometry args={[1.8, 0.8]} />
          <meshBasicMaterial color="#fbbf24" />
        </mesh>
      </group>

      {/* ═══════════════════════════════════════════════════════════════
          ZONE 3: CENTRAL ROTUNDA NURSE STATION (CENTER ATRIUM)
          ═══════════════════════════════════════════════════════════════ */}
      <group position={[-0.8, 0, 0]}>
        {/* Circular Porcelain Island Base */}
        <mesh position={[0, 0.02, 0]} receiveShadow>
          <cylinderGeometry args={[2.5, 2.5, 0.04, 32]} />
          <meshStandardMaterial color="#e0f2fe" roughness={0.3} />
        </mesh>

        {/* North Curved Nurse Counter Desk */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[2.1, 2.1, 1.1, 32, 1, false, Math.PI * 0.15, Math.PI * 0.7]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} side={2} />
        </mesh>
        {/* North Counter Top Rim (Medical Cyan) */}
        <mesh position={[0, 1.12, 0]}>
          <cylinderGeometry args={[2.2, 2.2, 0.06, 32, 1, false, Math.PI * 0.12, Math.PI * 0.76]} />
          <meshStandardMaterial color="#0284c7" side={2} />
        </mesh>

        {/* South Curved Nurse Counter Desk */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[2.1, 2.1, 1.1, 32, 1, false, Math.PI * 1.15, Math.PI * 0.7]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} side={2} />
        </mesh>
        {/* South Counter Top Rim (Medical Cyan) */}
        <mesh position={[0, 1.12, 0]}>
          <cylinderGeometry args={[2.2, 2.2, 0.06, 32, 1, false, Math.PI * 1.12, Math.PI * 0.76]} />
          <meshStandardMaterial color="#0284c7" side={2} />
        </mesh>

        {/* Center Workstation Pod & Multi-Displays */}
        <mesh position={[0, 0.5, 0]} castShadow>
          <boxGeometry args={[1.1, 1.0, 1.1]} />
          <meshStandardMaterial color="#f1f5f9" roughness={0.3} />
        </mesh>
        {/* 4 Diagnostic Monitors facing outwards */}
        {[-0.55, 0.55].map((x, i) => (
          <mesh key={`disp-x-${i}`} position={[x, 1.25, 0]}>
            <boxGeometry args={[0.05, 0.35, 0.45]} />
            <meshStandardMaterial color="#0f172a" />
          </mesh>
        ))}
        {[-0.55, 0.55].map((z, i) => (
          <mesh key={`disp-z-${i}`} position={[0, 1.25, z]}>
            <boxGeometry args={[0.45, 0.35, 0.05]} />
            <meshStandardMaterial color="#0f172a" />
          </mesh>
        ))}
      </group>

      {/* ═══════════════════════════════════════════════════════════════
          ZONE 4: NORTH WING (EXAM ROOMS, DOCTOR OFFICE, LABORATORY)
          ═══════════════════════════════════════════════════════════════ */}
      {/* North Exam Room 1 */}
      <group position={[-4.5, 0, -6.8]}>
        {/* Exam Table with Roll */}
        <mesh position={[0.8, 0.4, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.0, 0.5, 2.0]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.3} />
        </mesh>
        {/* Doctor Desk */}
        <mesh position={[-0.8, 0.45, -0.4]} castShadow>
          <boxGeometry args={[1.2, 0.9, 0.6]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} />
        </mesh>
        {/* Handwash Sink */}
        <mesh position={[-1.2, 0.85, 0.6]}>
          <boxGeometry args={[0.4, 0.25, 0.4]} />
          <meshStandardMaterial color="#f1f5f9" metalness={0.2} />
        </mesh>
      </group>

      {/* North Exam Room 2 */}
      <group position={[-1.2, 0, -6.8]}>
        <mesh position={[0.8, 0.4, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.0, 0.5, 2.0]} />
          <meshStandardMaterial color="#f8fafc" roughness={0.3} />
        </mesh>
        <mesh position={[-0.8, 0.45, -0.4]} castShadow>
          <boxGeometry args={[1.2, 0.9, 0.6]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} />
        </mesh>
        <mesh position={[-1.2, 0.85, 0.6]}>
          <boxGeometry args={[0.4, 0.25, 0.4]} />
          <meshStandardMaterial color="#f1f5f9" metalness={0.2} />
        </mesh>
      </group>

      {/* North Doctor Station Office */}
      <group position={[2.6, 0, -6.8]}>
        {/* Executive Physician Desk */}
        <mesh position={[0, 0.45, -0.2]} castShadow receiveShadow>
          <boxGeometry args={[1.8, 0.9, 0.9]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} />
        </mesh>
        <mesh position={[0, 0.92, -0.2]}>
          <boxGeometry args={[1.85, 0.04, 0.95]} />
          <meshStandardMaterial color="#38bdf8" />
        </mesh>
        {/* Dual 4K Medical Displays */}
        <mesh position={[-0.35, 1.25, -0.2]}>
          <boxGeometry args={[0.55, 0.38, 0.04]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
        <mesh position={[0.35, 1.25, -0.2]}>
          <boxGeometry args={[0.55, 0.38, 0.04]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
      </group>

      {/* Clinical Laboratory (Large Room) */}
      <group position={[7.8, 0, -6.8]}>
        {/* Central Double-Sided Island Workbench */}
        <mesh position={[0, 0.55, 0]} castShadow receiveShadow>
          <boxGeometry args={[3.2, 1.1, 1.2]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} metalness={0.1} />
        </mesh>
        <mesh position={[0, 1.12, 0]}>
          <boxGeometry args={[3.25, 0.05, 1.25]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        {/* Automated Hematology & Chemistry Analyzers */}
        <mesh position={[-0.8, 1.45, 0]}>
          <boxGeometry args={[0.9, 0.6, 0.7]} />
          <meshStandardMaterial color="#f1f5f9" metalness={0.3} roughness={0.2} />
        </mesh>
        {/* High-Speed Centrifuge Unit */}
        <mesh position={[0.8, 1.35, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.4, 16]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.7} />
        </mesh>
        {/* Laboratory Wash Sink */}
        <mesh position={[-1.8, 0.9, 0.8]}>
          <boxGeometry args={[0.5, 0.3, 0.5]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.8} />
        </mesh>
      </group>

      {/* ═══════════════════════════════════════════════════════════════
          ZONE 5: CENTRAL CORE (DOCTOR CONSULTATION & PHARMACY)
          ═══════════════════════════════════════════════════════════════ */}
      {/* Central Doctor Station */}
      <group position={[4.2, 0, 0.5]}>
        {/* Consultation Table */}
        <mesh position={[0, 0.45, 0]} castShadow receiveShadow>
          <boxGeometry args={[2.0, 0.9, 1.1]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} />
        </mesh>
        <mesh position={[0, 0.92, 0]}>
          <boxGeometry args={[2.05, 0.04, 1.15]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        {/* Chairs */}
        {[-0.6, 0.6].map((x, i) => (
          <mesh key={`doc-chair-${i}`} position={[x, 0.45, 0.8]}>
            <boxGeometry args={[0.45, 0.85, 0.45]} />
            <meshStandardMaterial color="#0369a1" />
          </mesh>
        ))}
      </group>

      {/* Pharmacy (110 SQ FT) */}
      <group position={[8.4, 0, 0.5]}>
        {/* Dispensing Counter facing Corridor */}
        <mesh position={[-0.8, 0.55, 0]} castShadow receiveShadow>
          <boxGeometry args={[0.7, 1.1, 2.4]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} />
        </mesh>
        <mesh position={[-0.8, 1.12, 0]}>
          <boxGeometry args={[0.75, 0.05, 2.45]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        {/* Medication Shelving Racks along Back Wall */}
        <mesh position={[1.2, 1.2, 0]} castShadow>
          <boxGeometry args={[0.3, 2.2, 2.6]} />
          <meshStandardMaterial color="#e2e8f0" metalness={0.4} />
        </mesh>
        {/* Color-coded Medicine Box Containers */}
        {[-0.8, -0.2, 0.4, 1.0].map((z, i) => (
          <mesh key={`med-box-${i}`} position={[1.0, 1.4, z]}>
            <boxGeometry args={[0.2, 0.25, 0.4]} />
            <meshStandardMaterial color={i % 2 === 0 ? '#38bdf8' : '#10b981'} />
          </mesh>
        ))}
      </group>

      {/* ═══════════════════════════════════════════════════════════════
          ZONE 6: SOUTH WING (4 EXAM ROOMS & RADIOLOGY)
          ═══════════════════════════════════════════════════════════════ */}
      {/* South Examination Rooms 1 to 4 */}
      {[-4.2, -1.4, 1.4, 4.2].map((xPos, idx) => (
        <group key={`s-exam-${idx}`} position={[xPos, 0, 6.8]}>
          {/* Clinical Examination Table */}
          <mesh position={[0.5, 0.4, 0]} castShadow receiveShadow>
            <boxGeometry args={[0.9, 0.5, 1.9]} />
            <meshStandardMaterial color="#f8fafc" roughness={0.3} />
          </mesh>
          {/* White Sanitary Paper Sheet */}
          <mesh position={[0.5, 0.66, 0]}>
            <boxGeometry args={[0.75, 0.03, 1.8]} />
            <meshStandardMaterial color="#ffffff" roughness={0.9} />
          </mesh>
          {/* Consultation Desk & Doctor Chair */}
          <mesh position={[-0.6, 0.45, -0.4]} castShadow>
            <boxGeometry args={[0.9, 0.9, 0.55]} />
            <meshStandardMaterial color="#ffffff" />
          </mesh>
          {/* Handwash Sink */}
          <mesh position={[-0.6, 0.85, 0.6]}>
            <boxGeometry args={[0.35, 0.2, 0.35]} />
            <meshStandardMaterial color="#f1f5f9" />
          </mesh>
        </group>
      ))}

      {/* Radiology CT Scanner Suite */}
      <group position={[7.8, 0, 6.8]}>
        {/* High-Tech CT Scanner Gantry Ring */}
        <mesh position={[0.4, 1.4, 0]} rotation={[0, Math.PI / 2, 0]} castShadow>
          <torusGeometry args={[1.15, 0.32, 16, 36]} />
          <meshStandardMaterial color="#ffffff" roughness={0.15} metalness={0.1} />
        </mesh>
        {/* Bore Interior Glow (Medical Sky Blue) */}
        <mesh position={[0.4, 1.4, 0]} rotation={[0, Math.PI / 2, 0]}>
          <cylinderGeometry args={[0.82, 0.82, 0.55, 32, 1, true]} />
          <meshBasicMaterial color="#38bdf8" />
        </mesh>
        {/* Motorized Scan Bed */}
        <mesh position={[0.4, 0.5, -0.8]} castShadow receiveShadow>
          <boxGeometry args={[0.8, 0.45, 1.8]} />
          <meshStandardMaterial color="#94a3b8" metalness={0.5} />
        </mesh>
        {/* Operator Console */}
        <mesh position={[-1.3, 0.45, 0.8]}>
          <boxGeometry args={[0.9, 0.9, 0.5]} />
          <meshStandardMaterial color="#ffffff" />
        </mesh>
        <mesh position={[-1.3, 1.25, 0.8]}>
          <boxGeometry args={[0.5, 0.35, 0.05]} />
          <meshStandardMaterial color="#0f172a" />
        </mesh>
      </group>

      {/* ═══════════════════════════════════════════════════════════════
          ZONE 7: EAST INPATIENT WING (4 PRIVATE PATIENT ROOMS)
          ═══════════════════════════════════════════════════════════════ */}
      {/* Patient Room 1 (North-East) */}
      <group position={[14.2, 0, -6.8]}>
        {/* Hospital Electric Inpatient Bed */}
        <mesh position={[0.3, 0.4, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.3, 0.45, 2.3]} />
          <meshStandardMaterial color="#ffffff" roughness={0.3} />
        </mesh>
        {/* Cyan Bed Rails */}
        <mesh position={[-0.38, 0.75, 0]}>
          <boxGeometry args={[0.04, 0.25, 1.6]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        <mesh position={[0.98, 0.75, 0]}>
          <boxGeometry args={[0.04, 0.25, 1.6]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        {/* IV Pole */}
        <mesh position={[-0.8, 1.1, -0.8]}>
          <cylinderGeometry args={[0.02, 0.02, 2.2]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.9} />
        </mesh>
        {/* Ensuite Bathroom Partition & Fixtures */}
        <mesh position={[-1.2, 0.7, 1.1]}>
          <boxGeometry args={[0.4, 0.5, 0.45]} />
          <meshStandardMaterial color="#f1f5f9" />
        </mesh>
      </group>

      {/* Patient Room 2 (Mid-North East) */}
      <group position={[14.2, 0, -2.4]}>
        <mesh position={[0.3, 0.4, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.3, 0.45, 2.3]} />
          <meshStandardMaterial color="#ffffff" roughness={0.3} />
        </mesh>
        <mesh position={[-0.38, 0.75, 0]}>
          <boxGeometry args={[0.04, 0.25, 1.6]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        <mesh position={[-0.8, 1.1, -0.8]}>
          <cylinderGeometry args={[0.02, 0.02, 2.2]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.9} />
        </mesh>
      </group>

      {/* Patient Room 3 (Mid-South East) */}
      <group position={[14.2, 0, 2.4]}>
        <mesh position={[0.3, 0.4, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.3, 0.45, 2.3]} />
          <meshStandardMaterial color="#ffffff" roughness={0.3} />
        </mesh>
        <mesh position={[-0.38, 0.75, 0]}>
          <boxGeometry args={[0.04, 0.25, 1.6]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        <mesh position={[-0.8, 1.1, -0.8]}>
          <cylinderGeometry args={[0.02, 0.02, 2.2]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.9} />
        </mesh>
      </group>

      {/* Patient Room 4 (South-East) */}
      <group position={[14.2, 0, 6.8]}>
        <mesh position={[0.3, 0.4, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.3, 0.45, 2.3]} />
          <meshStandardMaterial color="#ffffff" roughness={0.3} />
        </mesh>
        <mesh position={[-0.38, 0.75, 0]}>
          <boxGeometry args={[0.04, 0.25, 1.6]} />
          <meshStandardMaterial color="#0284c7" />
        </mesh>
        <mesh position={[-0.8, 1.1, -0.8]}>
          <cylinderGeometry args={[0.02, 0.02, 2.2]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.9} />
        </mesh>
        {/* Ensuite Bathroom */}
        <mesh position={[-1.2, 0.7, -1.1]}>
          <boxGeometry args={[0.4, 0.5, 0.45]} />
          <meshStandardMaterial color="#f1f5f9" />
        </mesh>
      </group>
    </group>
  );
};
