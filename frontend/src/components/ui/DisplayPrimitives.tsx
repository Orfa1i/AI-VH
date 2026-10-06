import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
} from 'lucide-react';

/* ---------- ProgressBar ---------- */
export interface ProgressBarProps {
  value: number; // 0 to 100
  variant?: 'primary' | 'spectrum' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  isIndeterminate?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  variant = 'primary',
  size = 'md',
  label,
  isIndeterminate = false,
}) => {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className="ak-progress-field">
      {label && (
        <div className="ak-progress-field__row">
          <span className="ak-progress-field__label">{label}</span>
          <span className="ak-progress-field__value ak-num">
            {isIndeterminate ? '...' : `${Math.round(clamped)}%`}
          </span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={isIndeterminate ? undefined : clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        className={[
          'ak-progress',
          variant !== 'primary' ? `ak-progress--${variant}` : '',
          size !== 'md' ? `ak-progress--${size}` : '',
          isIndeterminate ? 'is-indeterminate' : '',
        ]
          .filter(Boolean)
          .join(' ')}
        style={{ '--value': `${clamped}%` } as React.CSSProperties}
      >
        <div className="ak-progress__bar" />
      </div>
    </div>
  );
};

/* ---------- Alert ---------- */
export interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'danger';
  title?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  actions,
}) => {
  const icons = {
    info: <Info aria-hidden="true" />,
    success: <CheckCircle2 aria-hidden="true" />,
    warning: <AlertTriangle aria-hidden="true" />,
    danger: <AlertCircle aria-hidden="true" />,
  };

  return (
    <div
      role="alert"
      className={[
        'ak-alert',
        variant !== 'info' ? `ak-alert--${variant}` : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {icons[variant]}
      <div className="ak-alert__body">
        {title && <span className="ak-alert__title">{title}</span>}
        <div>{children}</div>
        {actions && <div className="ak-alert__actions">{actions}</div>}
      </div>
    </div>
  );
};

/* ---------- Table ---------- */
export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  children: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ className = '', children, ...props }) => (
  <div className="ak-table-wrap">
    <table className={`ak-table ${className}`} {...props}>
      {children}
    </table>
  </div>
);

/* ---------- Tabs ---------- */
export interface TabItem {
  id: string;
  label: string;
  count?: number | string;
}

export interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeId, onChange }) => (
  <div role="tablist" className="ak-tabs">
    {tabs.map((tab) => {
      const isSelected = tab.id === activeId;
      return (
        <button
          key={tab.id}
          role="tab"
          type="button"
          aria-selected={isSelected}
          className="ak-tab"
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {tab.count !== undefined && (
            <span className="ak-tab__count ak-num">({tab.count})</span>
          )}
        </button>
      );
    })}
  </div>
);

/* ---------- Stat ---------- */
export interface StatProps {
  label: string;
  value: string | number;
  delta?: string;
}

export const Stat: React.FC<StatProps> = ({ label, value, delta }) => (
  <div className="ak-stat">
    <span className="ak-stat__label">{label}</span>
    <span className="ak-stat__value ak-num">{value}</span>
    {delta && <span className="caption" style={{ color: 'var(--text-secondary)' }}>{delta}</span>}
  </div>
);

/* ---------- EmptyState ---------- */
export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
}) => (
  <div className="ak-empty">
    {icon && <div className="ak-empty__mark">{icon}</div>}
    <h3 className="ak-empty__title">{title}</h3>
    <p className="ak-empty__text">{description}</p>
    {action && <div style={{ marginTop: 8 }}>{action}</div>}
  </div>
);

/* ---------- Divider ---------- */
export const Divider: React.FC<{ isSpectrum?: boolean; className?: string }> = ({
  isSpectrum = false,
  className = '',
}) => (
  <hr
    className={[
      'ak-divider',
      isSpectrum ? 'ak-divider--spectrum' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ')}
  />
);
