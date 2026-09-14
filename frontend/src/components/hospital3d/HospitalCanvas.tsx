import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { DepartmentRoom } from './DepartmentRoom';
import { AgentAvatar } from './AgentAvatar';
import { HospitalFurnishings } from './HospitalFurnishings';
import { FirstPersonControls } from './FirstPersonControls';
import { FirstPersonHUD } from './FirstPersonHUD';

interface HospitalCanvasProps {
  activeDepartment: string;
  patientPos: [number, number, number];
  nursePos: [number, number, number];
  doctorPos: [number, number, number];
  patientAction: string;
  nurseAction: string;
  doctorAction: string;
  onDepartmentClick: (name: string) => void;
}

export const HospitalCanvas: React.FC<HospitalCanvasProps> = ({
  activeDepartment,
  patientPos,
  nursePos,
  doctorPos,
  patientAction,
  nurseAction,
  doctorAction,
  onDepartmentClick,
}) => {
  const [isFirstPerson, setIsFirstPerson] = useState(true);
  const [currentLocation, setCurrentLocation] = useState('Hospital Central Corridor');

  return (
    <div className="w-full h-full relative bg-slate-950 overflow-hidden isolate z-0">
      {/* 1st-Person Perspective HUD & Mode Toggle */}
      <FirstPersonHUD
        currentLocation={currentLocation}
        isFirstPerson={isFirstPerson}
        onTogglePerspective={() => setIsFirstPerson((prev) => !prev)}
      />

      <Canvas
        shadows
        camera={{ position: isFirstPerson ? [0, 1.7, 0] : [0, 18, 18], fov: isFirstPerson ? 65 : 45 }}
        className={`w-full h-full ${isFirstPerson ? 'cursor-crosshair' : 'cursor-grab active:cursor-grabbing'}`}
      >
        <color attach="background" args={['#090d16']} />
        <ambientLight intensity={0.7} />
        <directionalLight
          position={[12, 24, 15]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-20}
          shadow-camera-right={20}
          shadow-camera-top={20}
          shadow-camera-bottom={-20}
        />
        <pointLight position={[0, 8, 0]} intensity={0.5} color="#38bdf8" />

        <Suspense fallback={null}>
          {/* Main Hospital Floor Ground & Grid */}
          <Grid
            renderOrder={-1}
            position={[0, 0, 0]}
            infiniteGrid
            cellSize={1}
            cellThickness={0.5}
            cellColor="#1e293b"
            sectionSize={4}
            sectionThickness={1}
            sectionColor="#334155"
            fadeDistance={45}
          />

          {/* Central Corridor Floor Marker */}
          <mesh position={[0, 0.02, 0]} receiveShadow>
            <boxGeometry args={[22, 0.04, 3]} />
            <meshStandardMaterial color="#0f172a" roughness={0.8} />
          </mesh>

          {/* 3D Clinical Interior Furnishings */}
          <HospitalFurnishings />

          {/* --- DEPARTMENTS --- */}
          {/* Row 1 (North): Reception, Waiting Area, Nurse Station */}
          <DepartmentRoom
            name="Reception & Intake"
            code="RECEPTION"
            position={[-8, 0, -6]}
            size={[5, 1, 4.5]}
            floorColor="#1e293b"
            iconText="🏢"
            isActive={activeDepartment === 'RECEPTION'}
            onClick={() => onDepartmentClick('RECEPTION')}
          />

          <DepartmentRoom
            name="Waiting Area"
            code="WAITING_AREA"
            position={[-2, 0, -6]}
            size={[5, 1, 4.5]}
            floorColor="#1e293b"
            iconText="🪑"
            isActive={activeDepartment === 'WAITING_AREA'}
            onClick={() => onDepartmentClick('WAITING_AREA')}
          />

          <DepartmentRoom
            name="Nurse Station & Triage"
            code="NURSE_STATION"
            position={[6, 0, -6]}
            size={[7, 1, 4.5]}
            floorColor="#0f766e"
            iconText="🩺"
            isActive={activeDepartment === 'NURSE_STATION'}
            onClick={() => onDepartmentClick('NURSE_STATION')}
          />

          {/* Row 2 (Middle): Examination Rooms, Doctor Station */}
          <DepartmentRoom
            name="Examination Room 1"
            code="EXAMINATION_ROOM_1"
            position={[-7, 0, 1]}
            size={[5.5, 1, 4.5]}
            floorColor="#1e3a8a"
            iconText="🛌"
            isActive={activeDepartment === 'EXAMINATION_ROOM_1' || activeDepartment === 'EXAMINATION'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_1')}
          />

          <DepartmentRoom
            name="Examination Room 2"
            code="EXAMINATION_ROOM_2"
            position={[-0.5, 0, 1]}
            size={[5.5, 1, 4.5]}
            floorColor="#1e293b"
            iconText="🛌"
            isActive={activeDepartment === 'EXAMINATION_ROOM_2'}
            onClick={() => onDepartmentClick('EXAMINATION_ROOM_2')}
          />

          <DepartmentRoom
            name="Doctor Station (Internal Med)"
            code="DOCTOR_STATION"
            position={[6.5, 0, 1]}
            size={[6.5, 1, 4.5]}
            floorColor="#1e1b4b"
            iconText="👨‍⚕️"
            isActive={activeDepartment === 'DOCTOR_STATION'}
            onClick={() => onDepartmentClick('DOCTOR_STATION')}
          />

          {/* Row 3 (South): Laboratory, Radiology, Pharmacy */}
          <DepartmentRoom
            name="Clinical Laboratory"
            code="LABORATORY"
            position={[-7, 0, 8]}
            size={[5.5, 1, 4.5]}
            floorColor="#312e81"
            iconText="🧪"
            isActive={activeDepartment === 'LABORATORY'}
            onClick={() => onDepartmentClick('LABORATORY')}
          />

          <DepartmentRoom
            name="Radiology (CT / X-Ray)"
            code="RADIOLOGY"
            position={[-0.5, 0, 8]}
            size={[5.5, 1, 4.5]}
            floorColor="#3730a3"
            iconText="☢️"
            isActive={activeDepartment === 'RADIOLOGY'}
            onClick={() => onDepartmentClick('RADIOLOGY')}
          />

          <DepartmentRoom
            name="Pharmacy"
            code="PHARMACY"
            position={[6.5, 0, 8]}
            size={[6.5, 1, 4.5]}
            floorColor="#1e293b"
            iconText="💊"
            isActive={activeDepartment === 'PHARMACY'}
            onClick={() => onDepartmentClick('PHARMACY')}
          />

          {/* --- AGENT AVATARS --- */}
          {/* Patient Agent */}
          <AgentAvatar
            id="patient_agent"
            name="Patient"
            role="PATIENT"
            targetPosition={patientPos}
            currentAction={patientAction}
            color="#d97706"
          />

          {/* Nurse Agent */}
          <AgentAvatar
            id="nurse_agent"
            name="Sarah Jenkins, RN"
            role="NURSE"
            targetPosition={nursePos}
            currentAction={nurseAction}
            color="#06b6d4"
          />

          {/* Doctor Agent (Internal Medicine / MedGemma) */}
          <AgentAvatar
            id="doctor_agent"
            name="Dr. Vance, MD (MedGemma)"
            role="DOCTOR"
            targetPosition={doctorPos}
            currentAction={doctorAction}
            color="#10b981"
          />

          {/* Laboratory Scientist Agent */}
          <AgentAvatar
            id="lab_agent"
            name="David Chen, MLS"
            role="LAB"
            targetPosition={[-7, 0, 8]}
            currentAction="Processing Biomarker Assays"
            color="#a855f7"
          />

          {/* Radiologist Agent */}
          <AgentAvatar
            id="rad_agent"
            name="Dr. Hayes, MD"
            role="RADIOLOGY"
            targetPosition={[-0.5, 0, 8]}
            currentAction="Reading Diagnostic Studies"
            color="#6366f1"
          />

          {/* Perspective Controls */}
          {isFirstPerson ? (
            <FirstPersonControls
              enabled={isFirstPerson}
              onLocationChange={(loc) => setCurrentLocation(loc)}
            />
          ) : (
            <OrbitControls
              enableDamping
              dampingFactor={0.08}
              maxPolarAngle={Math.PI / 2.1}
              minDistance={8}
              maxDistance={38}
            />
          )}
        </Suspense>
      </Canvas>
    </div>
  );
};
