import React from 'react';
import { PolicyBenchmarkPage } from './PolicyBenchmarkPage';

export interface PolicyBenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PolicyBenchmarkModal: React.FC<PolicyBenchmarkModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-[var(--ak-color-text-primary)]/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-6xl bg-white border border-[var(--ak-color-border-subtle)] rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[92vh] max-h-[95vh] text-[var(--ak-color-text-primary)]">
        <PolicyBenchmarkPage isModal={true} onClose={onClose} />
      </div>
    </div>
  );
};

export default PolicyBenchmarkModal;
