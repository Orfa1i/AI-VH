import React from 'react';
import type { VitalSigns } from '../../types';
import { Heart, Activity, Wind, Thermometer, AlertCircle } from 'lucide-react';

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
      <div className="absolute top-20 right-4 z-20 w-80 bg-slate-900/80 backdrop-blur-md rounded-xl border border-slate-800 p-4 shadow-2xl">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase">
          <Activity className="w-4 h-4 text-slate-500" />
          <span>Patient Telemetry Monitor</span>
        </div>
        <div className="text-slate-500 text-xs mt-3 text-center py-4 border border-dashed border-slate-800 rounded-lg">
          No active patient on telemetry
        </div>
      </div>
    );
  }

  return (
    <div className="absolute top-20 right-4 z-20 w-84 bg-slate-950/90 backdrop-blur-md rounded-xl border border-slate-800 p-4 shadow-2xl font-mono text-slate-200">
      {/* Top Banner */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-bold text-slate-300 tracking-wide truncate max-w-[160px]">
            {patientName}
          </span>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
          LEAD II • ECG ON
        </span>
      </div>

      {/* Simulated ECG Sweep Line */}
      <div className="h-9 w-full bg-slate-900/60 rounded border border-slate-800/80 mb-3 flex items-center justify-center overflow-hidden relative">
        <svg className="w-full h-full text-emerald-500" viewBox="0 0 200 40" preserveAspectRatio="none">
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
        <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-800/50">
          <div className="flex items-center justify-between text-[11px] text-emerald-400">
            <span className="flex items-center gap-1 font-sans font-semibold">
              <Heart className="w-3.5 h-3.5 fill-emerald-500/20" /> HR
            </span>
            <span className="text-[10px]">bpm</span>
          </div>
          <div className="text-2xl font-black text-emerald-300 mt-1">
            {vitals.heart_rate}
          </div>
        </div>

        {/* Blood Pressure */}
        <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-800/50">
          <div className="flex items-center justify-between text-[11px] text-rose-400">
            <span className="flex items-center gap-1 font-sans font-semibold">
              <Activity className="w-3.5 h-3.5" /> NIBP
            </span>
            <span className="text-[10px]">mmHg</span>
          </div>
          <div className="text-xl font-black text-rose-300 mt-1">
            {vitals.systolic_bp}/{vitals.diastolic_bp}
          </div>
        </div>

        {/* SpO2 */}
        <div className="p-2.5 rounded-lg bg-cyan-950/30 border border-cyan-800/50">
          <div className="flex items-center justify-between text-[11px] text-cyan-400">
            <span className="flex items-center gap-1 font-sans font-semibold">
              <Wind className="w-3.5 h-3.5" /> SpO2
            </span>
            <span className="text-[10px]">%</span>
          </div>
          <div className="text-2xl font-black text-cyan-300 mt-1">
            {vitals.spo2_percent}%
          </div>
        </div>

        {/* Respiratory Rate & Temp */}
        <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/50">
          <div className="flex items-center justify-between text-[11px] text-amber-400">
            <span className="flex items-center gap-1 font-sans font-semibold">
              <Thermometer className="w-3.5 h-3.5" /> RR / TEMP
            </span>
          </div>
          <div className="text-sm font-bold text-amber-300 mt-1">
            {vitals.respiratory_rate}/m • {vitals.temperature_c.toFixed(1)}°C
          </div>
        </div>
      </div>

      {/* Pain Indicator */}
      <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
        <span className="flex items-center gap-1">
          <AlertCircle className="w-3 h-3 text-amber-400" /> Patient Pain Score
        </span>
        <span className="font-bold text-amber-300 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/60">
          {vitals.pain_score} / 10
        </span>
      </div>
    </div>
  );
};
