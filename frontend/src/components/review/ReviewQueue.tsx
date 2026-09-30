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
      <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-md text-center">
        <h2 className="px-4 pb-2 text-xs font-mono font-bold uppercase tracking-wide text-slate-900">
          Review queue
        </h2>
        <p className="text-sm text-slate-600 font-sans">No reports awaiting review.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-md overflow-hidden">
      <h2 className="px-4 py-3 text-xs font-mono font-bold uppercase tracking-wide text-slate-900 border-b border-slate-200">
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
                  selected ? 'bg-sky-50' : 'hover:bg-slate-100'
                }`}
              >
                <span className="text-xs font-mono font-semibold text-slate-900">{item.case_id}</span>
                {item.flagged && (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-100 text-red-800 border border-red-300">
                    <AlertTriangle className="w-3 h-3" />
                    FLAGGED
                  </span>
                )}
                <span className="ml-auto text-[11px] font-mono text-slate-600">{item.status}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
