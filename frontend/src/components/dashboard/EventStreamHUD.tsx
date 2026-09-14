import React, { useRef, useEffect } from 'react';
import type { HospitalEvent } from '../../types';
import { Activity, Radio, ChevronDown, ChevronUp } from 'lucide-react';

interface EventStreamHUDProps {
  events: HospitalEvent[];
  isConnected: boolean;
}

export const EventStreamHUD: React.FC<EventStreamHUDProps> = ({ events, isConnected }) => {
  const [isExpanded, setIsExpanded] = React.useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const getEventBadge = (type: string) => {
    if (type.includes('ARRIVED')) return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    if (type.includes('TRIAGE') || type.includes('VITALS')) return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
    if (type.includes('DOCTOR') || type.includes('EXAM')) return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    if (type.includes('RAG')) return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
    if (type.includes('LAB')) return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
    if (type.includes('DIAGNOSIS') || type.includes('TREATMENT')) return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
    if (type.includes('REPORT')) return 'bg-emerald-500/30 text-emerald-200 border-emerald-400';
    return 'bg-slate-700/50 text-slate-300 border-slate-600';
  };

  return (
    <div className="absolute bottom-4 left-4 z-20 w-96 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800 shadow-2xl overflow-hidden transition-all duration-300">
      {/* Header */}
      <div
        className="px-4 py-2.5 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-sky-400 animate-pulse" />
          <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Hospital Event Stream
          </span>
          <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-700 text-slate-300">
            <Radio className={`w-2.5 h-2.5 ${isConnected ? 'text-emerald-400' : 'text-rose-400'}`} />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
        <button className="text-slate-400 hover:text-white">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {/* Events List */}
      {isExpanded && (
        <div ref={scrollRef} className="max-h-64 overflow-y-auto p-3 space-y-2 text-xs">
          {events.length === 0 ? (
            <div className="text-slate-500 text-center py-6">Awaiting simulation events...</div>
          ) : (
            events.map((evt, idx) => (
              <div
                key={evt.id || idx}
                className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold border ${getEventBadge(
                      evt.event_type
                    )}`}
                  >
                    {evt.event_type}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-slate-300 leading-snug">{evt.summary}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
