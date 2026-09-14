import React from 'react';
import { Compass, Eye, Layers, Sparkles } from 'lucide-react';
import type { ProximityTarget } from './FirstPersonControls';

interface FirstPersonHUDProps {
  currentLocation: string;
  isFirstPerson: boolean;
  onTogglePerspective: () => void;
  activeStation?: ProximityTarget | null;
  onInteract?: (stationId: string) => void;
}

export const FirstPersonHUD: React.FC<FirstPersonHUDProps> = ({
  currentLocation,
  isFirstPerson,
  onTogglePerspective,
  activeStation,
  onInteract,
}) => {
  return (
    <>
      {/* Reticle / Crosshair in Center (First-Person Only) */}
      {isFirstPerson && (
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-10">
          <div className="w-5 h-5 rounded-full border border-sky-400/50 flex items-center justify-center">
            <div className="w-1 h-1 rounded-full bg-sky-300 shadow-sm shadow-sky-400" />
          </div>
        </div>
      )}

      {/* Perspective Switcher & Location Banner (Top Center) */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
        {/* Current Location Badge */}
        {isFirstPerson && (
          <div className="px-3.5 py-1.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-700/80 text-xs text-slate-200 shadow-xl flex items-center gap-2 font-semibold">
            <Compass className="w-4 h-4 text-emerald-400 animate-spin" style={{ animationDuration: '10s' }} />
            <span className="text-slate-400">Location:</span>
            <span className="text-emerald-300 font-bold">{currentLocation}</span>
          </div>
        )}

        {/* Perspective Mode Switcher Button */}
        <button
          onClick={onTogglePerspective}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-xl border flex items-center gap-2 transition-all cursor-pointer ${
            isFirstPerson
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 shadow-emerald-500/20'
              : 'bg-slate-900/90 hover:bg-slate-800 text-slate-200 border-slate-700'
          }`}
        >
          {isFirstPerson ? (
            <>
              <Eye className="w-4 h-4" />
              <span>1st-Person Walkthrough</span>
            </>
          ) : (
            <>
              <Layers className="w-4 h-4" />
              <span>Overhead Orbit View</span>
            </>
          )}
          <span className="text-[10px] opacity-75 font-mono">
            ({isFirstPerson ? 'Active' : 'Click for 1st-Person'})
          </span>
        </button>
      </div>

      {/* Interactive Proximity Trigger Banner (Appears when near an agent / station) */}
      {isFirstPerson && activeStation && (
        <div className="absolute bottom-16 left-1/2 -translate-x-1/2 z-30 animate-in fade-in slide-in-from-bottom-3 duration-200">
          <button
            onClick={() => onInteract && onInteract(activeStation.id)}
            className="px-4 py-2.5 rounded-2xl bg-gradient-to-r from-emerald-600/95 to-teal-600/95 hover:from-emerald-500 hover:to-teal-500 backdrop-blur-md border border-emerald-300/80 text-white shadow-2xl shadow-emerald-500/40 flex items-center gap-3 font-semibold text-xs transition-all cursor-pointer transform hover:scale-105 active:scale-95"
          >
            <span className="w-6 h-6 rounded-lg bg-black/40 border border-white/40 flex items-center justify-center font-mono font-black text-white text-[13px] shadow-inner">
              E
            </span>
            <div className="text-left">
              <div className="text-white font-bold tracking-tight">{activeStation.actionPrompt}</div>
              <div className="text-[10px] text-emerald-100 font-normal">{activeStation.name}</div>
            </div>
            <Sparkles className="w-4 h-4 text-emerald-200 animate-pulse ml-1" />
          </button>
        </div>
      )}

      {/* Walking Controls Prompt Bar (Bottom Center in First Person) */}
      {isFirstPerson && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 px-4 py-2 rounded-xl bg-slate-900/80 backdrop-blur-md border border-slate-800 text-[11px] text-slate-300 shadow-xl flex items-center gap-4 pointer-events-none font-mono">
          <div className="flex items-center gap-1.5">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 font-bold">
              W A S D
            </span>
            <span className="text-slate-400">Walk</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 font-bold">
              Drag Mouse
            </span>
            <span className="text-slate-400">Look</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 font-bold">
              Shift
            </span>
            <span className="text-slate-400">Sprint</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-600 text-emerald-300 font-bold">
              E
            </span>
            <span className="text-emerald-400">Interact</span>
          </div>
        </div>
      )}
    </>
  );
};
