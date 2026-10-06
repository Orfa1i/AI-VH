import React from 'react';
import type { VitalSigns } from '../../types';
import { Heart, Activity, Wind, Thermometer, AlertCircle } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface VitalsMonitorHUDProps {
  vitals?: VitalSigns | null;
  patientName?: string;
}

export const VitalsMonitorHUD: React.FC<VitalsMonitorHUDProps> = ({
  vitals,
  patientName = 'Patient in Bay 1',
}) => {
  if (!vitals) {
    return (
      <Card className="absolute top-20 right-4 z-20 w-80 p-4 shadow-lg">
        <div className="flex items-center gap-2 text-xs font-semibold text-[var(--ak-color-text-muted)] uppercase tracking-wider">
          <Activity className="w-4 h-4 text-[var(--ak-color-text-muted)]" />
          <span>Patient telemetry monitor</span>
        </div>
        <div className="text-[var(--ak-color-text-muted)] text-xs mt-3 text-center py-4 border border-dashed border-[var(--ak-color-border-subtle)] rounded-lg">
          No active patient on telemetry
        </div>
      </Card>
    );
  }

  return (
    <Card className="absolute top-20 right-4 z-20 w-84 p-4 shadow-lg font-mono text-[var(--ak-color-text-primary)]">
      {/* Top Banner */}
      <div className="flex items-center justify-between border-b border-[var(--ak-color-border-subtle)] pb-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[var(--ak-color-success)] animate-pulse" />
          <span className="text-xs font-semibold text-[var(--ak-color-text-primary)] tracking-wide truncate max-w-[160px]">
            {patientName}
          </span>
        </div>
        <Badge variant="success" size="sm">
          Lead II • ECG ON
        </Badge>
      </div>

      {/* Simulated ECG Sweep Line */}
      <div className="h-9 w-full bg-[var(--ak-color-text-primary)] rounded-lg mb-3 flex items-center justify-center overflow-hidden relative">
        <svg className="w-full h-full text-emerald-300" viewBox="0 0 200 40" preserveAspectRatio="none">
          <path
            d="M 0 20 L 30 20 L 35 12 L 40 28 L 45 4 L 50 36 L 55 20 L 70 20 L 80 15 L 90 20 L 130 20 L 135 12 L 140 28 L 145 4 L 150 36 L 155 20 L 170 20 L 180 15 L 200 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          />
        </svg>
      </div>

      {/* Grid of 4 Core Vitals */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* Heart Rate */}
        <div className="p-2.5 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
          <div className="flex items-center justify-between text-[11px] text-[var(--ak-color-text-secondary)]">
            <span className="flex items-center gap-1 font-sans font-medium">
              <Heart className="w-3.5 h-3.5 text-[var(--ak-color-success)]" /> HR
            </span>
            <span className="text-[10px] text-[var(--ak-color-text-muted)]">bpm</span>
          </div>
          <div className="text-2xl font-bold text-[var(--ak-color-success)] mt-1 tabular-nums">
            {vitals.heart_rate}
          </div>
        </div>

        {/* Blood Pressure */}
        <div className="p-2.5 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
          <div className="flex items-center justify-between text-[11px] text-[var(--ak-color-text-secondary)]">
            <span className="flex items-center gap-1 font-sans font-medium">
              <Activity className="w-3.5 h-3.5 text-[var(--ak-color-danger)]" /> NIBP
            </span>
            <span className="text-[10px] text-[var(--ak-color-text-muted)]">mmHg</span>
          </div>
          <div className="text-xl font-bold text-[var(--ak-color-text-primary)] mt-1 tabular-nums">
            {vitals.systolic_bp}/{vitals.diastolic_bp}
          </div>
        </div>

        {/* SpO2 */}
        <div className="p-2.5 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
          <div className="flex items-center justify-between text-[11px] text-[var(--ak-color-text-secondary)]">
            <span className="flex items-center gap-1 font-sans font-medium">
              <Wind className="w-3.5 h-3.5 text-[var(--ak-color-primary)]" /> SpO2
            </span>
            <span className="text-[10px] text-[var(--ak-color-text-muted)]">%</span>
          </div>
          <div className="text-2xl font-bold text-[var(--ak-color-primary)] mt-1 tabular-nums">
            {vitals.spo2_percent}%
          </div>
        </div>

        {/* Respiratory Rate & Temp */}
        <div className="p-2.5 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)]">
          <div className="flex items-center justify-between text-[11px] text-[var(--ak-color-text-secondary)]">
            <span className="flex items-center gap-1 font-sans font-medium">
              <Thermometer className="w-3.5 h-3.5 text-[var(--ak-color-warning)]" /> RR / Temp
            </span>
          </div>
          <div className="text-xs font-semibold text-[var(--ak-color-text-primary)] mt-1 tabular-nums">
            {vitals.respiratory_rate}/m • {vitals.temperature_c.toFixed(1)}°C
          </div>
        </div>
      </div>

      {/* Pain Indicator */}
      <div className="mt-2.5 pt-2 border-t border-[var(--ak-color-border-subtle)] flex items-center justify-between text-[11px] text-[var(--ak-color-text-muted)]">
        <span className="flex items-center gap-1">
          <AlertCircle className="w-3 h-3 text-[var(--ak-color-warning)]" /> Patient pain score
        </span>
        <Badge variant={vitals.pain_score > 5 ? 'danger' : 'warning'} size="sm">
          {vitals.pain_score} / 10
        </Badge>
      </div>
    </Card>
  );
};
