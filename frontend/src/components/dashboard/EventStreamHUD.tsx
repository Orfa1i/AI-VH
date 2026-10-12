import React, { useRef, useEffect } from 'react';
import type { HospitalEvent } from '../../types';
import { Activity, Radio, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

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

  const getEventBadgeVariant = (type: string): 'primary' | 'success' | 'warning' | 'danger' | 'neutral' => {
    if (type.includes('ARRIVED')) return 'warning';
    if (type.includes('TRIAGE') || type.includes('VITALS')) return 'primary';
    if (type.includes('DOCTOR') || type.includes('EXAM')) return 'primary';
    if (type.includes('RAG')) return 'primary';
    if (type.includes('LAB')) return 'primary';
    if (type.includes('DIAGNOSIS') || type.includes('TREATMENT')) return 'warning';
    if (type.includes('REPORT')) return 'success';
    return 'neutral';
  };

  return (
    <Card className="absolute bottom-4 left-4 z-20 w-96 shadow-lg overflow-hidden transition-all duration-300">
      {/* Header */}
      <div
        className="px-4 py-2.5 bg-[var(--ak-color-bg-subtle)] border-b border-[var(--ak-color-border-subtle)] flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[var(--ak-color-primary)] animate-pulse" />
          <span className="text-xs font-semibold text-[var(--ak-color-text-primary)] uppercase tracking-wider">
            Hospital event stream
          </span>
          <Badge variant={isConnected ? 'success' : 'danger'} size="sm">
            <Radio className="w-2.5 h-2.5 mr-1" />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </Badge>
        </div>
        <button className="text-[var(--ak-color-text-muted)] hover:text-[var(--ak-color-text-primary)] cursor-pointer">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {/* Events List */}
      {isExpanded && (
        <div ref={scrollRef} className="max-h-64 overflow-y-auto p-3 space-y-2 text-xs">
          {events.length === 0 ? (
            <div className="text-[var(--ak-color-text-muted)] text-center py-6 font-mono text-[11px]">
              Awaiting clinical simulation events...
            </div>
          ) : (
            events.map((evt, idx) => (
              <div
                key={evt.id || idx}
                className="p-2 rounded-lg bg-[var(--ak-color-bg-subtle)] border border-[var(--ak-color-border-subtle)] hover:border-[var(--ak-color-border-strong)] transition-colors"
              >
                <div className="flex items-center justify-between gap-1 mb-1">
                  <Badge variant={getEventBadgeVariant(evt.event_type)} size="sm">
                    {evt.event_type}
                  </Badge>
                  <span className="text-[10px] text-[var(--ak-color-text-muted)] font-mono">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-[var(--ak-color-text-primary)] leading-snug">{evt.summary}</p>
              </div>
            ))
          )}
        </div>
      )}
    </Card>
  );
};
