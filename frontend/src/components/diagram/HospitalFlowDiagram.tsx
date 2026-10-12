import React, { useEffect, useRef } from 'react';
import type { BenchmarkCase, HospitalEvent, VitalSigns } from '../../types';

export interface HospitalFlowDiagramProps {
  cases?: BenchmarkCase[];
  selectedCaseId?: string;
  onSelectCase?: (caseId: string) => void;
  onRunSimulation?: () => void;
  isRunning?: boolean;
  activeDepartment?: string;
  doctorAction?: string;
  events?: HospitalEvent[];
  activeVitals?: VitalSigns | null;
  onOpenDepartmentStation?: (stationId: string) => void;
  onToggleTo3D?: () => void;
  onNavigateTab?: (tab: string) => void;
  onBackToPortal?: () => void;
}

export const HospitalFlowDiagram: React.FC<HospitalFlowDiagramProps> = ({
  onNavigateTab,
  onBackToPortal,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (e.data && e.data.type === 'NAVIGATE') {
        if (e.data.tab === 'PORTAL' || e.data.tab === 'LANDING') {
          onBackToPortal?.();
        } else if (onNavigateTab) {
          onNavigateTab(e.data.tab);
        }
      } else if (e.data && (e.data.type === 'PATIENT_ADMITTED' || e.data.type === 'REFRESH_PATIENTS')) {
        if (iframeRef.current && iframeRef.current.contentWindow) {
          iframeRef.current.contentWindow.postMessage(e.data, '*');
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onNavigateTab, onBackToPortal]);

  return (
    <div className="w-full flex-1 flex flex-col h-full min-h-[920px] bg-[#F7F8FB] relative isolate overflow-hidden">
      <iframe
        ref={iframeRef}
        src="/case-room.html"
        title="Virtual Hospital Case Room"
        className="w-full flex-1 border-0"
        style={{
          width: '100%',
          minHeight: 'calc(100vh - 60px)',
          height: '100%',
          border: 'none',
          display: 'block',
          background: '#F7F8FB',
        }}
      />
    </div>
  );
};

export default HospitalFlowDiagram;
