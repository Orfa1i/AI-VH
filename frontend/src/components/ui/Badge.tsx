import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'neutral' | 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'outline' | 'ai';
  hasDot?: boolean;
  children?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  hasDot = false,
  className = '',
  children,
  ...props
}) => {
  const classNames = [
    'ak-badge',
    variant !== 'neutral' ? `ak-badge--${variant}` : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <span className={classNames} {...props}>
      {hasDot && <span className="ak-badge__dot" aria-hidden="true" />}
      {children}
    </span>
  );
};

export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isSelected?: boolean;
  onRemove?: () => void;
  children?: React.ReactNode;
}

export const Chip: React.FC<ChipProps> = ({
  isSelected = false,
  onRemove,
  className = '',
  children,
  ...props
}) => {
  const classNames = [
    'ak-chip',
    isSelected ? 'is-selected' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type="button"
      className={classNames}
      aria-pressed={isSelected}
      {...props}
    >
      {children}
      {onRemove && (
        <span
          role="button"
          tabIndex={0}
          aria-label="Remove filter"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.stopPropagation();
              onRemove();
            }
          }}
          style={{ display: 'inline-flex', marginLeft: 4 }}
        >
          ×
        </span>
      )}
    </button>
  );
};
