import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  actions,
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleId = React.useId();

  // Escape key and focus management
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="ak-scrim"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="ak-dialog"
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 id={titleId} className="ak-dialog__title">
              {title}
            </h2>
            {description && <p className="ak-dialog__body" style={{ marginTop: 4 }}>{description}</p>}
          </div>
          <button
            type="button"
            className="ak-btn ak-btn--ghost ak-btn--sm ak-btn--icon"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X aria-hidden="true" style={{ width: 18, height: 18 }} />
          </button>
        </div>

        <div className="ak-dialog__body" style={{ marginTop: 8 }}>
          {children}
        </div>

        {actions && <div className="ak-dialog__foot">{actions}</div>}
      </div>
    </div>
  );
};
