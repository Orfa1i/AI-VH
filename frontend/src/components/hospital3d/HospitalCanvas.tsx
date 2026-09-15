import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { DepartmentRoom } from './DepartmentRoom';
import { AgentAvatar } from './AgentAvatar';
import { HospitalFurnishings } from './HospitalFurnishings';
import { FirstPersonControls } from './FirstPersonControls';
import type { ProximityTarget } from './FirstPersonControls';
import { FirstPersonHUD } from './FirstPersonHUD';

interface HospitalCanvasProps {
  activeDepartment: string;
  doctorPos: [number, number, number];
  doctorAction: string;
  onDepartmentClick: (name: string) => void;
  onStationInteract?: (stationId: string) => void;
}

export const HospitalCanvas: React.FC<HospitalCanvasProps> = ({
  activeDepartment,
  doctorPos: _doctorPos,
  doctorAction,
  onDepartmentClick,
  onStationInteract,
}) => {
  const [isFirstPerson, setIsFirstPerson] = useState(true);
  const [currentLocation, setCurrentLocation] = useState('Patient Waiting Area (Main Lobby)');
  const [activeProximityStation, setActiveProximityStation] = useState<ProximityTarget | null>(null);

  return (
    <div className="w-full h-full relative bg-sky-50/40 overflow-hidden isolate z-0">
      {/* 1st-Person Perspective HUD & Mode Switcher */}
      <FirstPersonHUD
        currentLocation={currentLocation}
        isFirstPerson={isFirstPerson}
        onTogglePerspective={() => setIsFirstPerson((prev) => !prev)}
        activeStation={activeProximityStation}
        onInteract={onStationInteract}
      />

      <Canvas
        shadows
        camera={{
          position: isFirstPerson ? [-13.5, 1.7, 0] : [0, 24, 20],
          fov: isFirstPerson ? 65 : 45,
        }}
        className={`w-full h-full ${
          isFirstPerson ? 'cursor-crosshair' : 'cursor-grab active:cursor-grabbing'
        }`}
      >
        {/* Crisp Medical Daylight Environment */}
        <color attach="background" args={['#f0f9ff']} />
        <ambientLight intensity={1.15} color="#ffffff" />
        <directionalLight
          position={[20, 32, 20]}
          intensity={1.35}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-25}
          shadow-camera-right={25}
          shadow-camera-top={25}
          shadow-camera-bottom={-25}
        />
        <directionalLight position={[-20, 22, -20]} intensity={0.45} color="#e0f2fe" />
        <pointLight position={[0, 9, 0]} intensity={0.6} color="#38bdf8" />

        <Suspense fallback={null}>
          {/* Main Hospital Porcelain Ground Slab */}
          <mesh position={[0, -0.01, 0]} receiveShadow>
            <boxGeometry args={[36.5, 0.05, 23.0]} />
            <meshStandardMaterial color="#f8fafc" roughness={0.3} metalness={0.05} />
          </mesh>

          {/* Clean Medical Ceramic Floor Grid */}
          <Grid
            renderOrder={-1}
            position={[0, 0.01, 0]}
            infiniteGrid={false}
            args={[36.0, 22.5]}
            cellSize={1.2}
            cellThickness={0.4}
            cellColor="#e2e8f0"
            sectionSize={3.6}
            sectionThickness={1.0}
            sectionColor="#cbd5e1"
            fadeDistance={55}
          />

          {/* ═══════════════════════════════════════════════════════════════
              ARCHITECTURAL CORRIDOR RUNNERS (LIGHT CLINICAL CYAN ACCENT)
              ═══════════════════════════════════════════════════════════════ */}
          {/* Central North Corridor Runner */}
          <mesh position={[-0.5, 0.02, -3.2]} receiveShadow>
            <boxGeometry args={[19.5, 0.02, 1.8]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.4} />
          </mesh>

          {/* Central South Corridor Runner */}
          <mesh position={[-0.5, 0.02, 3.2]} receiveShadow>
            <boxGeometry args={[19.5, 0.02, 1.8]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.4} />
          </mesh>

          {/* West Lobby & Waiting Area Floor Runner */}
          <mesh position={[-12.8, 0.02, 0]} receiveShadow>
            <boxGeometry args={[7.0, 0.02, 3.2]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.4} />
          </mesh>

          {/* East Inpatient Corridor Runner */}
          <mesh position={[11.2, 0.02, 0]} receiveShadow>
            <boxGeometry args={[2.2, 0.02, 18.0]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.4} />
          </mesh>

          {/* Blue Guide Border Ribbons */}
          {[-3.9, -2.5, 2.5, 3.9].map((z, idx) => (
            <mesh key={`ribbon-${idx}`} position={[-0.5, 0.03, z]}>
              <boxGeometry args={[19.5, 0.01, 0.06]} />
              <meshBasicMaterial color="#0284c7" />
            </mesh>
          ))}

          {/* ═══════════════════════════════════════════════════════════════
              EXTERIOR BUILDING PERIMETER & MAIN ENTRANCE
              ═══════════════════════════════════════════════════════════════ */}
          {/* Main Entrance Double Glass Doors on West Wall */}
          <group position={[-18.1, 0, 0]}>
            <mesh position={[0, 1.25, 0]}>
              <boxGeometry args={[0.1, 2.5, 2.4]} />
              <meshStandardMaterial color="#38bdf8" opacity={0.6} transparent roughness={0.1} />
            </mesh>
            <mesh position={[0, 2.55, 0]}>
              <boxGeometry args={[0.2, 0.1, 2.5]} />
              <meshStandardMaterial color="#0f172a" />
            </mesh>
          </group>

          {/* ═══════════════════════════════════════════════════════════════
              3D CLINICAL INTERIOR FURNISHINGS (AUTOCAD BLUEPRINT SHEET A-1)
              ═══════════════════════════════════════════════════════════════ */}
          <HospitalFurnishings />

          {/* ═══════════════════════════════════════════════════════════════
              DEPARTMENTS & ROOMS (AUTOCAD SHEET A-1 EXACT LAYOUT)
              ═══════════════════════════════════════════════════════════════ */}

          {/* --- WEST ZONE: RECEPTION, WAITING AREA, EMERGENCY DEPARTMENT --- */}
          <DepartmentRoom
            name="Reception & Intake"
            code="RECEPTION"
            position={[-12.8, 0, -6.8]}
            size={[7.0, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🏢"
            doorSide="south"
            isActive={activeDepartment === 'RECEPTION'}
            onClick={() => onDepartmentClick('RECEPTION')}
          />

          <DepartmentRoom
            name="Patient Waiting Area"
            code="WAITING_AREA"
            position={[-12.8, 0, -0.6]}
            size={[7.0, 1.35, 5.0]}
            floorColor="#f1f5f9"
            wallColor="#ffffff"
            iconText="🪑"
            doorSide="open"
            isActive={activeDepartment === 'WAITING_AREA'}
            onClick={() => onDepartmentClick('WAITING_AREA')}
          />

          <DepartmentRoom
            name="Emergency Department (ED)"
            code="EMERGENCY_DEPARTMENT"
            position={[-12.8, 0, 6.8]}
            size={[7.0, 1.35, 6.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🚨"
            doorSide="open"
            isActive={activeDepartment === 'EMERGENCY_DEPARTMENT'}
            onClick={() => onDepartmentClick('EMERGENCY_DEPARTMENT')}
          />

          <DepartmentRoom
            name="Triage & Ambulance Bay"
            code="TRIAGE"
            position={[-8.5, 0, 7.8]}
            size={[2.2, 1.35, 4.2]}
            floorColor="#fef3c7"
            wallColor="#ffffff"
            iconText="🚑"
            doorSide="open"
            isActive={activeDepartment === 'TRIAGE'}
            onClick={() => onDepartmentClick('TRIAGE')}
          />

          {/* --- CENTER HUB: CENTRAL ROTUNDA NURSE STATION --- */}
          <DepartmentRoom
            name="Central Rotunda Nurse Station"
            code="NURSE_STATION"
            position={[-0.8, 0, 0]}
            size={[5.5, 1.35, 5.5]}
            floorColor="#e0f2fe"
            wallColor="#ffffff"
            iconText="🩺"
            doorSide="open"
            isActive={activeDepartment === 'NURSE_STATION'}
            onClick={() => onDepartmentClick('NURSE_STATION')}
          />

          {/* --- NORTH WING: EXAM ROOMS 1-2, DOCTOR OFFICE, CLINICAL LABORATORY --- */}
          <DepartmentRoom
            name="Examination Room 1"
            code="EXAMINATION_ROOM_1"
            position={[-4.5, 0, -6.8]}
            size={[3.0, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛌"
            doorSide="south"
            isActive={activeDepartment === 'EXAMINATION_ROOM_1' || activeDepartment === 'EXAMINATION'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_1')}
          />

          <DepartmentRoom
            name="Examination Room 2"
            code="EXAMINATION_ROOM_2"
            position={[-1.2, 0, -6.8]}
            size={[3.0, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛌"
            doorSide="south"
            isActive={activeDepartment === 'EXAMINATION_ROOM_2'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_2')}
          />

          <DepartmentRoom
            name="Doctor Station (Internal Med)"
            code="DOCTOR_STATION_NORTH"
            position={[2.6, 0, -6.8]}
            size={[4.0, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="👨‍⚕️"
            doorSide="south"
            isActive={activeDepartment === 'DOCTOR_STATION' || activeDepartment === 'DOCTOR_STATION_NORTH'}
            onClick={() => onDepartmentClick('DOCTOR_STATION')}
          />

          <DepartmentRoom
            name="Clinical Laboratory"
            code="LABORATORY"
            position={[7.8, 0, -6.8]}
            size={[5.6, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🧪"
            doorSide="south"
            isActive={activeDepartment === 'LABORATORY'}
            onClick={() => onDepartmentClick('LABORATORY')}
          />

          {/* --- CENTRAL CORE: CONSULTATION SUITE & PHARMACY --- */}
          <DepartmentRoom
            name="Doctor Station (Consultation)"
            code="DOCTOR_STATION_CENTER"
            position={[4.2, 0, 0.5]}
            size={[4.2, 1.35, 4.0]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="📋"
            doorSide="north"
            isActive={activeDepartment === 'DOCTOR_STATION_CENTER'}
            onClick={() => onDepartmentClick('DOCTOR_STATION_CENTER')}
          />

          <DepartmentRoom
            name="Pharmacy"
            code="PHARMACY"
            position={[8.4, 0, 0.5]}
            size={[3.8, 1.35, 4.0]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="💊"
            doorSide="north"
            isActive={activeDepartment === 'PHARMACY'}
            onClick={() => onDepartmentClick('PHARMACY')}
          />

          {/* --- SOUTH WING: EXAM ROOMS 3-6 & RADIOLOGY --- */}
          <DepartmentRoom
            name="Examination Room 3"
            code="EXAMINATION_ROOM_3"
            position={[-4.2, 0, 6.8]}
            size={[2.6, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛌"
            doorSide="north"
            isActive={activeDepartment === 'EXAMINATION_ROOM_3'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_3')}
          />

          <DepartmentRoom
            name="Examination Room 4"
            code="EXAMINATION_ROOM_4"
            position={[-1.4, 0, 6.8]}
            size={[2.6, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛌"
            doorSide="north"
            isActive={activeDepartment === 'EXAMINATION_ROOM_4'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_4')}
          />

          <DepartmentRoom
            name="Examination Room 5"
            code="EXAMINATION_ROOM_5"
            position={[1.4, 0, 6.8]}
            size={[2.6, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛌"
            doorSide="north"
            isActive={activeDepartment === 'EXAMINATION_ROOM_5'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_5')}
          />

          <DepartmentRoom
            name="Examination Room 6"
            code="EXAMINATION_ROOM_6"
            position={[4.2, 0, 6.8]}
            size={[2.6, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛌"
            doorSide="north"
            isActive={activeDepartment === 'EXAMINATION_ROOM_6'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_6')}
          />

          <DepartmentRoom
            name="Radiology (CT & X-Ray Suite)"
            code="RADIOLOGY"
            position={[7.8, 0, 6.8]}
            size={[4.2, 1.35, 5.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="☢️"
            doorSide="north"
            isActive={activeDepartment === 'RADIOLOGY'}
            onClick={() => onDepartmentClick('RADIOLOGY')}
          />

          {/* --- EAST INPATIENT WING: 4 PRIVATE PATIENT ROOMS --- */}
          <DepartmentRoom
            name="Patient Room 1"
            code="PATIENT_ROOM_1"
            position={[14.5, 0, -7.2]}
            size={[4.5, 1.35, 4.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛏️"
            doorSide="west"
            isActive={activeDepartment === 'PATIENT_ROOM_1'}
            onClick={() => onDepartmentClick('PATIENT_ROOM_1')}
          />

          <DepartmentRoom
            name="Patient Room 2"
            code="PATIENT_ROOM_2"
            position={[14.5, 0, -2.4]}
            size={[4.5, 1.35, 4.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛏️"
            doorSide="west"
            isActive={activeDepartment === 'PATIENT_ROOM_2'}
            onClick={() => onDepartmentClick('PATIENT_ROOM_2')}
          />

          <DepartmentRoom
            name="Patient Room 3"
            code="PATIENT_ROOM_3"
            position={[14.5, 0, 2.4]}
            size={[4.5, 1.35, 4.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛏️"
            doorSide="west"
            isActive={activeDepartment === 'PATIENT_ROOM_3'}
            onClick={() => onDepartmentClick('PATIENT_ROOM_3')}
          />

          <DepartmentRoom
            name="Patient Room 4"
            code="PATIENT_ROOM_4"
            position={[14.5, 0, 7.2]}
            size={[4.5, 1.35, 4.2]}
            floorColor="#f8fafc"
            wallColor="#ffffff"
            iconText="🛏️"
            doorSide="west"
            isActive={activeDepartment === 'PATIENT_ROOM_4'}
            onClick={() => onDepartmentClick('PATIENT_ROOM_4')}
          />

          {/* ═══════════════════════════════════════════════════════════════
              AGENT AVATARS (IM-ONLY SCOPE: ONLY THE INTERNAL MEDICINE PHYSICIAN
              IS RENDERED. Patient/Nurse/Lab/Radiology/Pharmacist avatars were
              removed pending real testing per project scope decision.)
              ═══════════════════════════════════════════════════════════════ */}
          {/* Doctor Agent (In North Doctor Station Office) */}
          <AgentAvatar
            id="doctor_agent"
            name="Internal Medicine Physician"
            role="DOCTOR"
            targetPosition={_doctorPos || [2.6, 0, -6.8]}
            currentAction={doctorAction}
            color="#10b981"
            rotation={[0, Math.PI, 0]}
          />


          {/* ═══════════════════════════════════════════════════════════════
              PERSPECTIVE CONTROLS
              ═══════════════════════════════════════════════════════════════ */}
          {isFirstPerson ? (
            <FirstPersonControls
              enabled={isFirstPerson}
              onLocationChange={(loc) => setCurrentLocation(loc)}
              onProximityChange={(station) => setActiveProximityStation(station)}
              onInteract={onStationInteract}
            />
          ) : (
            <OrbitControls
              enableDamping
              dampingFactor={0.08}
              maxPolarAngle={Math.PI / 2.1}
              minDistance={10}
              maxDistance={50}
              target={[0, 0, 0]}
            />
          )}
        </Suspense>
      </Canvas>
    </div>
  );
};
