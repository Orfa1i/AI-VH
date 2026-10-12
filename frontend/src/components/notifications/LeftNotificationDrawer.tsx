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
    if (type.includes('DISCHARGE') || type.includes('ENCOUNTER_CLOSED'))
      return <CheckCircle2 aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--success-600)' }} />;
    if (type.includes('REPORT'))
      return <FileText aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--indigo-500)' }} />;
    if (type.includes('TRIAGE') || type.includes('VITALS'))
      return <Activity aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--info-600)' }} />;
    if (type.includes('DOCTOR') || type.includes('EXAM'))
      return <Stethoscope aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--indigo-500)' }} />;
    if (type.includes('LAB'))
      return <FlaskConical aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--spectrum-azure)' }} />;
    if (type.includes('PHARMACY') || type.includes('TREATMENT'))
      return <Pill aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--warning-600)' }} />;
    if (type.includes('ARRIVED'))
      return <User aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--indigo-500)' }} />;
    return <AlertTriangle aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--neutral-500)' }} />;
  };

  const filteredEvents = events.filter((evt) => {
    if (activeFilter === 'REPORTS') return evt.event_type.includes('REPORT');
    if (activeFilter === 'TRIAGE') return evt.event_type.includes('TRIAGE') || evt.event_type.includes('VITALS');
    if (activeFilter === 'CLINICAL')
      return evt.event_type.includes('DOCTOR') || evt.event_type.includes('LAB') || evt.event_type.includes('PHARMACY');
    return true;
  });

  return (
    <>
      {/* 1. DOCKED LEFT TRIGGER PILL */}
      <div style={{ position: 'fixed', left: 0, top: 96, zIndex: 'var(--z-sticky)' }}>
        <button
          onClick={handleOpenDrawer}
          type="button"
          title="Open Hospital Event Notifications"
          aria-label="Open Hospital Event Notifications"
          className="ak-btn ak-btn--secondary ak-btn--sm"
          style={{
            borderTopLeftRadius: 0,
            borderBottomLeftRadius: 0,
            borderLeft: 0,
            paddingLeft: 'var(--space-3)',
            paddingRight: 'var(--space-4)',
            boxShadow: 'var(--shadow-sm)',
            background: 'var(--bg-surface)',
          }}
        >
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Bell aria-hidden="true" style={{ width: 16, height: 16, color: 'var(--text-brand)' }} />
            {unreadCount > 0 && (
              <span
                className="ak-num"
                style={{
                  position: 'absolute',
                  top: -6,
                  right: -8,
                  minWidth: 16,
                  height: 16,
                  borderRadius: 'var(--radius-pill)',
                  background: 'var(--danger-600)',
                  color: 'var(--neutral-0)',
                  fontSize: 12,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0 4px',
                }}
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </div>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Notifications</span>
          <ChevronRight aria-hidden="true" style={{ width: 14, height: 14, color: 'var(--text-secondary)' }} />
        </button>
      </div>

      {/* 2. TRANSIENT FLOATING TOAST */}
      {activeToast && !isOpen && (
        <div
          role="status"
          style={{
            position: 'fixed',
            left: 'var(--space-6)',
            top: 96,
            zIndex: 'var(--z-toast)',
          }}
        >
          <div className="ak-toast">
            {getEventIcon(activeToast.event_type)}
            <div className="ak-toast__text">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                <span className="caption" style={{ color: 'var(--indigo-200)', textTransform: 'uppercase' }}>
                  {activeToast.event_type.replace(/_/g, ' ')}
                </span>
                <span className="ak-num" style={{ fontSize: 12, color: 'var(--neutral-300)' }}>
                  {activeToast.timestamp
                    ? new Date(activeToast.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    : 'Now'}
                </span>
              </div>
              <p style={{ margin: '2px 0 0', fontSize: 13, lineHeight: '18px' }}>
                {activeToast.summary || 'Clinical encounter update recorded.'}
              </p>
            </div>
            {activeToast.event_type.includes('REPORT') && onNavigateToTab && (
              <button
                type="button"
                className="ak-toast__action"
                onClick={() => {
                  onNavigateToTab('REPORTS');
                  setActiveToast(null);
                }}
              >
                View
              </button>
            )}
            <button
              type="button"
              className="ak-btn ak-btn--ghost ak-btn--sm ak-btn--icon"
              style={{ color: 'var(--neutral-0)' }}
              onClick={() => setActiveToast(null)}
              aria-label="Dismiss toast"
            >
              <X aria-hidden="true" style={{ width: 16, height: 16 }} />
            </button>
          </div>
        </div>
      )}

      {/* 3. DOCKED NOTIFICATION DRAWER */}
      {isOpen && (
        <div
          role="presentation"
          className="ak-scrim"
          style={{ justifyContent: 'flex-start', padding: 0 }}
          onClick={handleCloseDrawer}
        >
          <aside
            role="dialog"
            aria-label="Hospital Event Feed"
            aria-modal="true"
            className="ak-card"
            style={{
              width: 'min(360px, 100vw)',
              height: '100vh',
              borderRadius: 0,
              padding: 0,
              display: 'flex',
              flexDirection: 'column',
              boxShadow: 'var(--shadow-lg)',
              animation: 'none',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div
              style={{
                padding: 'var(--space-4) var(--space-5)',
                borderBottom: '1px solid var(--border-default)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                <Activity aria-hidden="true" style={{ width: 20, height: 20, color: 'var(--indigo-500)' }} />
                <div>
                  <h2 className="heading-3" style={{ fontSize: 16, lineHeight: '22px' }}>Hospital Event Feed</h2>
                  <span className="caption" style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Radio aria-hidden="true" style={{ width: 12, height: 12, color: isConnected ? 'var(--success-600)' : 'var(--neutral-400)' }} />
                    {isConnected ? 'Telemetry Stream Active' : 'Disconnected'}
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="ak-btn ak-btn--ghost ak-btn--sm ak-btn--icon"
                onClick={handleCloseDrawer}
                aria-label="Close feed"
              >
                <ChevronLeft aria-hidden="true" style={{ width: 20, height: 20 }} />
              </button>
            </div>

            {/* Filter Row */}
            <div
              style={{
                padding: 'var(--space-2) var(--space-4)',
                borderBottom: '1px solid var(--border-default)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'var(--bg-subtle)',
              }}
            >
              <div className="ak-seg">
                {(['ALL', 'REPORTS', 'TRIAGE', 'CLINICAL'] as const).map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    aria-pressed={activeFilter === filter}
                    className="ak-seg__item"
                    style={{ fontSize: 12, height: 26, padding: '0 8px' }}
                    onClick={() => setActiveFilter(filter)}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              {events.length > 0 && onClearEvents && (
                <button
                  type="button"
                  className="ak-btn ak-btn--ghost ak-btn--sm"
                  style={{ fontSize: 12, padding: '0 8px', color: 'var(--danger-600)' }}
                  onClick={onClearEvents}
                >
                  <Trash2 aria-hidden="true" style={{ width: 14, height: 14 }} />
                  Clear
                </button>
              )}
            </div>

            {/* Event List */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
                background: 'var(--bg-page)',
              }}
            >
              {filteredEvents.length === 0 ? (
                <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  <Activity aria-hidden="true" style={{ width: 32, height: 32, margin: '0 auto 8px', opacity: 0.4 }} />
                  <p className="body-sm">No hospital notifications recorded.</p>
                </div>
              ) : (
                [...filteredEvents].reverse().map((evt, idx) => (
                  <div
                    key={evt.id || `${evt.event_type}-${idx}-${evt.timestamp || 'ts'}`}
                    className="ak-card ak-card--subtle"
                    style={{
                      padding: 'var(--space-3)',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-default)',
                    }}
                  >
                    <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
                      <div
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-subtle)',
                          display: 'grid',
                          placeItems: 'center',
                          flexShrink: 0,
                        }}
                      >
                        {getEventIcon(evt.event_type)}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 6, marginBottom: 2 }}>
                          <span className="caption" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {evt.event_type.replace(/_/g, ' ')}
                          </span>
                          <span className="ak-num caption" style={{ color: 'var(--text-tertiary)' }}>
                            {evt.timestamp
                              ? new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                              : ''}
                          </span>
                        </div>
                        <p className="body-sm" style={{ color: 'var(--text-secondary)' }}>
                          {evt.summary || 'Clinical simulation event dispatched.'}
                        </p>
                        {evt.event_type.includes('REPORT') && onNavigateToTab && (
                          <div style={{ marginTop: 8 }}>
                            <button
                              type="button"
                              className="ak-btn ak-btn--ghost ak-btn--sm"
                              style={{ padding: '0 8px', height: 26, fontSize: 12 }}
                              onClick={() => {
                                onNavigateToTab('REPORTS');
                                handleCloseDrawer();
                              }}
                            >
                              Inspect in Clinical Review &rarr;
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                borderTop: '1px solid var(--border-default)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'var(--bg-surface)',
              }}
            >
              <span className="caption" style={{ color: 'var(--text-tertiary)' }}>
                Total: <strong className="ak-num" style={{ color: 'var(--text-primary)' }}>{events.length}</strong>
              </span>
              <button
                type="button"
                className="ak-btn ak-btn--secondary ak-btn--sm"
                onClick={handleCloseDrawer}
              >
                Close feed
              </button>
            </div>
          </aside>
        </div>
      )}
    </>
  );
};
