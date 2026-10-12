import React from 'react';
import { AlertTriangle } from 'lucide-react';
import type { QueueItem } from './api';

interface ReviewQueueProps {
  items: QueueItem[];
  selectedId: string | null;
  onSelect: (originalId: string) => void;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ items, selectedId, onSelect }) => {
  if (items.length === 0) {
    return (
      <div className="p-6 bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md text-center">
        <h2 className="px-4 pb-2 text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)]">
          Review queue
        </h2>
        <p className="text-sm text-[var(--ak-color-text-secondary)] font-sans">No reports awaiting review.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md overflow-hidden">
      <h2 className="px-4 py-3 text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)] border-b border-[var(--ak-color-border-subtle)]">
        Review queue
      </h2>
      <ul className="divide-y divide-slate-200">
        {items.map((item) => {
          const selected = item.original_id === selectedId;
          return (
            <li key={item.assignment_id}>
              <button
                type="button"
                onClick={() => onSelect(item.original_id)}
                aria-current={selected ? 'true' : undefined}
                className={`w-full px-4 py-3 flex items-center gap-3 text-left transition cursor-pointer ${
                  selected ? 'bg-[var(--ak-color-primary-soft)]' : 'hover:bg-[var(--ak-color-bg-subtle)]'
                }`}
              >
                <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-primary)]">{item.case_id}</span>
                {item.flagged && (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-danger)] border border-[var(--ak-color-border-subtle)]">
                    <AlertTriangle className="w-3 h-3" />
                    FLAGGED
                  </span>
                )}
                <span className="ml-auto text-[11px] font-mono text-[var(--ak-color-text-secondary)]">{item.status}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
