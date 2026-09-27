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
    if (type.includes('ARRIVED')) return 'bg-amber-50 text-amber-800 border-amber-300';
    if (type.includes('TRIAGE') || type.includes('VITALS')) return 'bg-cyan-50 text-cyan-800 border-cyan-300';
    if (type.includes('DOCTOR') || type.includes('EXAM')) return 'bg-emerald-50 text-emerald-800 border-emerald-300';
    if (type.includes('RAG')) return 'bg-purple-50 text-purple-800 border-purple-300';
    if (type.includes('LAB')) return 'bg-blue-50 text-blue-800 border-blue-300';
    if (type.includes('DIAGNOSIS') || type.includes('TREATMENT')) return 'bg-rose-50 text-rose-800 border-rose-300';
    if (type.includes('REPORT')) return 'bg-emerald-50 text-emerald-800 border-emerald-400';
    return 'bg-slate-100 text-slate-700 border-slate-300';
  };

  return (
    <div className="absolute bottom-4 left-4 z-20 w-96 bg-white/95 backdrop-blur-md rounded-xl border border-slate-200 shadow-xl overflow-hidden transition-all duration-300">
      {/* Header */}
      <div
        className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-sky-600 animate-pulse" />
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Hospital Event Stream
          </span>
          <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200/80 text-slate-700 font-mono font-medium">
            <Radio className={`w-2.5 h-2.5 ${isConnected ? 'text-emerald-600' : 'text-rose-600'}`} />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
        <button className="text-slate-400 hover:text-slate-700">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {/* Events List */}
      {isExpanded && (
        <div ref={scrollRef} className="max-h-64 overflow-y-auto p-3 space-y-2 text-xs">
          {events.length === 0 ? (
            <div className="text-slate-400 text-center py-6 font-mono text-[11px]">Awaiting clinical simulation events...</div>
          ) : (
            events.map((evt, idx) => (
              <div
                key={evt.id || idx}
                className="p-2 rounded-lg bg-slate-50 border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold border ${getEventBadge(
                      evt.event_type
                    )}`}
                  >
                    {evt.event_type}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-slate-800 leading-snug">{evt.summary}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
