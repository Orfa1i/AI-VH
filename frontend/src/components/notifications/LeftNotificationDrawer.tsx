import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Bell,
  ChevronLeft,
  ChevronRight,
  X,
  CheckCircle2,
  AlertTriangle,
  Stethoscope,
  FlaskConical,
  Pill,
  FileText,
  User,
  Radio,
  Trash2,
} from 'lucide-react';
import type { HospitalEvent } from '../../types';

interface LeftNotificationDrawerProps {
  events: HospitalEvent[];
  isConnected?: boolean;
  onNavigateToTab?: (tab: string) => void;
  onClearEvents?: () => void;
}

export const LeftNotificationDrawer: React.FC<LeftNotificationDrawerProps> = ({
  events,
  isConnected = true,
  onNavigateToTab,
  onClearEvents,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'REPORTS' | 'TRIAGE' | 'CLINICAL'>('ALL');
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeToast, setActiveToast] = useState<HospitalEvent | null>(null);
  const toastTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastEventCountRef = useRef(events.length);

  // Detect incoming events to trigger slide-in toast and increment unread badge
  useEffect(() => {
    if (events.length > lastEventCountRef.current) {
      const newEvent = events[events.length - 1];
      setUnreadCount((prev) => prev + (events.length - lastEventCountRef.current));
      
      // Trigger toast slide-in from left
      setActiveToast(newEvent);
      if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = setTimeout(() => {
        setActiveToast(null);
      }, 5000);
    }
    lastEventCountRef.current = events.length;

    return () => {
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, [events]);

  const handleOpenDrawer = () => {
    setIsOpen(true);
    setUnreadCount(0);
    setActiveToast(null);
  };

  const handleCloseDrawer = () => {
    setIsOpen(false);
  };

  const getEventIcon = (type: string) => {
    if (type.includes('DISCHARGE') || type.includes('ENCOUNTER_CLOSED')) return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />;
    if (type.includes('REPORT')) return <FileText className="w-3.5 h-3.5 text-emerald-600" />;
    if (type.includes('TRIAGE') || type.includes('VITALS')) return <Activity className="w-3.5 h-3.5 text-cyan-600" />;
    if (type.includes('DOCTOR') || type.includes('EXAM')) return <Stethoscope className="w-3.5 h-3.5 text-sky-600" />;
    if (type.includes('LAB')) return <FlaskConical className="w-3.5 h-3.5 text-blue-600" />;
    if (type.includes('PHARMACY') || type.includes('TREATMENT')) return <Pill className="w-3.5 h-3.5 text-amber-600" />;
    if (type.includes('ARRIVED')) return <User className="w-3.5 h-3.5 text-indigo-600" />;
    return <AlertTriangle className="w-3.5 h-3.5 text-slate-500" />;
  };

  const getCategoryColor = (type: string) => {
    if (type.includes('DISCHARGE') || type.includes('ENCOUNTER_CLOSED')) return 'border-emerald-200 bg-emerald-50/70 text-emerald-900';
    if (type.includes('REPORT')) return 'border-emerald-200 bg-emerald-50/70 text-emerald-900';
    if (type.includes('TRIAGE') || type.includes('VITALS')) return 'border-cyan-200 bg-cyan-50/70 text-cyan-900';
    if (type.includes('DOCTOR') || type.includes('EXAM')) return 'border-sky-200 bg-sky-50/70 text-sky-900';
    if (type.includes('LAB')) return 'border-blue-200 bg-blue-50/70 text-blue-900';
    if (type.includes('PHARMACY') || type.includes('TREATMENT')) return 'border-amber-200 bg-amber-50/70 text-amber-900';
    return 'border-slate-200 bg-slate-50 text-slate-800';
  };

  const filteredEvents = events.filter((evt) => {
    if (activeFilter === 'REPORTS') return evt.event_type.includes('REPORT');
    if (activeFilter === 'TRIAGE') return evt.event_type.includes('TRIAGE') || evt.event_type.includes('VITALS');
    if (activeFilter === 'CLINICAL') return evt.event_type.includes('DOCTOR') || evt.event_type.includes('LAB') || evt.event_type.includes('PHARMACY');
    return true;
  });

  return (
    <>
      {/* ═══════════════════════════════════════════════════════════════════
          1. SLIDING LEFT DOCK TRIGGER BUTTON (Always accessible on left edge)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="fixed left-0 top-36 z-40">
        <button
          onClick={handleOpenDrawer}
          className={`flex items-center gap-2 pl-2 pr-3 py-2 bg-white/95 hover:bg-white text-slate-800 border-y border-r border-slate-300 shadow-md rounded-r-xl transition-all duration-300 hover:shadow-lg hover:pr-4 cursor-pointer backdrop-blur-md group ${
            unreadCount > 0 ? 'border-sky-400 ring-2 ring-sky-400/20' : ''
          }`}
          title="Open Hospital Event Notifications"
        >
          <div className="relative">
            <Bell className="w-4 h-4 text-sky-600 group-hover:scale-110 transition-transform" />
            {unreadCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-rose-500 text-white font-mono text-[9px] font-bold flex items-center justify-center animate-pulse shadow-xs">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </div>
          <span className="text-[11px] font-mono font-bold tracking-wider text-slate-700 uppercase hidden sm:inline">
            Notifications
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          2. SLIDE-IN LIVE TOAST NOTIFICATION (Appears from left edge)
          ═══════════════════════════════════════════════════════════════════ */}
      <div
        className={`fixed left-4 top-24 z-50 transition-all duration-500 ease-out transform ${
          activeToast && !isOpen ? 'translate-x-0 opacity-100 pointer-events-auto' : '-translate-x-full opacity-0 pointer-events-none'
        }`}
      >
        {activeToast && (
          <div className="w-84 p-3.5 rounded-xl bg-white/95 backdrop-blur-md border border-slate-200 shadow-2xl hud-bracket flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
              {getEventIcon(activeToast.event_type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-sky-800 truncate">
                  {activeToast.event_type.replace(/_/g, ' ')}
                </span>
                <span className="text-[9px] font-mono text-slate-400 shrink-0">
                  {activeToast.timestamp ? new Date(activeToast.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'JUST NOW'}
                </span>
              </div>
              <p className="text-xs text-slate-700 font-medium leading-snug line-clamp-2">
                {activeToast.summary || 'Clinical encounter update recorded.'}
              </p>
              {activeToast.event_type.includes('REPORT') && onNavigateToTab && (
                <button
                  onClick={() => {
                    onNavigateToTab('REPORTS');
                    setActiveToast(null);
                  }}
                  className="mt-2 text-[10px] font-mono font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1 underline underline-offset-2 cursor-pointer"
                >
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  <span>View Pending Report in Clinical Review &rarr;</span>
                </button>
              )}
            </div>
            <button
              onClick={() => setActiveToast(null)}
              className="text-slate-400 hover:text-slate-700 p-0.5 rounded cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          3. FULL SLIDE-OUT LEFT NOTIFICATION DRAWER (Panel from left)
          ═══════════════════════════════════════════════════════════════════ */}
      {/* Backdrop */}
      {isOpen && (
        <div
          onClick={handleCloseDrawer}
          className="fixed inset-0 bg-slate-900/20 backdrop-blur-xs z-50 transition-opacity duration-300"
        />
      )}

      {/* Drawer Container */}
      <aside
        className={`fixed top-0 left-0 bottom-0 w-88 sm:w-96 bg-white border-r border-slate-200 shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Drawer Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700 shadow-xs">
              <Activity className="w-4 h-4 text-sky-600" />
            </div>
            <div>
              <h3 className="text-xs font-mono font-bold text-slate-900 uppercase tracking-wide">
                Hospital Event Feed
              </h3>
              <p className="text-[10px] font-mono text-slate-500 flex items-center gap-1.5">
                <Radio className={`w-2.5 h-2.5 ${isConnected ? 'text-emerald-500 animate-pulse' : 'text-slate-400'}`} />
                <span>{isConnected ? 'Telemetry Stream Active' : 'Disconnected'}</span>
              </p>
            </div>
          </div>
          <button
            onClick={handleCloseDrawer}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition cursor-pointer"
            title="Close Drawer"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Pills & Actions */}
        <div className="px-4 py-2.5 border-b border-slate-200 flex items-center justify-between bg-white text-xs font-mono">
          <div className="flex items-center gap-1">
            {(['ALL', 'REPORTS', 'TRIAGE', 'CLINICAL'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`px-2 py-1 rounded text-[10px] font-bold transition cursor-pointer ${
                  activeFilter === filter
                    ? 'bg-sky-50 text-sky-700 border border-sky-300 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {filter}
              </button>
            ))}
          </div>

          {events.length > 0 && onClearEvents && (
            <button
              onClick={onClearEvents}
              className="text-[10px] text-slate-400 hover:text-rose-600 flex items-center gap-1 transition cursor-pointer"
              title="Clear Notification History"
            >
              <Trash2 className="w-3 h-3" />
              <span>Clear</span>
            </button>
          )}
        </div>

        {/* Notification Event List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5 bg-slate-50/50">
          {filteredEvents.length === 0 ? (
            <div className="py-16 text-center text-slate-400 font-mono text-xs">
              <Activity className="w-8 h-8 text-slate-300 mx-auto mb-2 opacity-50" />
              <p>No hospital notifications recorded.</p>
              <p className="text-[10px] text-slate-400 mt-1">Events will appear live during clinical encounters.</p>
            </div>
          ) : (
            [...filteredEvents].reverse().map((evt, idx) => (
              <div
                key={evt.id || `${evt.event_type}-${idx}-${evt.timestamp || 'ts'}`}
                className={`p-3 rounded-xl border transition-all duration-200 bg-white shadow-2xs hover:shadow-xs ${getCategoryColor(
                  evt.event_type
                )}`}
              >
                <div className="flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-md bg-white border border-slate-200 flex items-center justify-center shrink-0 mt-0.5 shadow-2xs">
                    {getEventIcon(evt.event_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider truncate">
                        {evt.event_type.replace(/_/g, ' ')}
                      </span>
                      <span className="text-[9px] font-mono text-slate-400 shrink-0">
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 font-medium leading-relaxed break-words">
                      {evt.summary || 'Clinical simulation event dispatched.'}
                    </p>
                    {evt.event_type.includes('REPORT') && onNavigateToTab && (
                      <button
                        onClick={() => {
                          onNavigateToTab('REPORTS');
                          handleCloseDrawer();
                        }}
                        className="mt-2 text-[10px] font-mono font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1 underline underline-offset-2 cursor-pointer"
                      >
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>Inspect in Clinical Review</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-3 border-t border-slate-200 bg-white flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span>Total Logged: <strong className="text-slate-800">{events.length}</strong></span>
          <button
            onClick={handleCloseDrawer}
            className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg border border-slate-200 transition cursor-pointer"
          >
            Close Feed
          </button>
        </div>
      </aside>
    </>
  );
};
