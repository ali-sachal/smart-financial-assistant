import React, { useState } from 'react';
import { AlertTriangle, Database } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { endpoints, ApiError } from '../../api';

interface DemoSeedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (itemCount: number) => void;
}

export const DemoSeedModal: React.FC<DemoSeedModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSeed = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await endpoints.demo.seed();
      if (response.result.seeded) {
        onSuccess(response.result.item_count);
        onClose();
      } else {
        setError('Failed to seed demo data. Server returned false.');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`[${err.code}] ${err.message}${err.requestId ? ` (Request: ${err.requestId})` : ''}`);
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error during demo seed.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2.5 text-amber-400">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>Reset & Seed Demo Data</span>
        </div>
      }
      description="Destructive development action: Replaces current partition data"
    >
      <div className="space-y-4">
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 leading-relaxed">
          <p className="font-semibold text-amber-300 mb-1">Warning: Irreversible action</p>
          Calling <code className="px-1.5 py-0.5 rounded bg-amber-900/40 text-amber-300 font-mono text-[11px]">POST /demo/seed</code> will purge all transactions, budgets, receipts, and bills in your authenticated user partition and insert 20 deterministic demo records.
        </div>

        <div className="space-y-2 text-xs text-slate-300">
          <p className="font-medium text-slate-200">This will populate:</p>
          <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1">
            <li>Checking account with standard opening balance</li>
            <li>20 deterministic transactions across groceries, dining, utilities</li>
            <li>Scheduled monthly bills & upcoming income flows</li>
            <li>Category budget ceilings with real-time velocity calculations</li>
          </ul>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <Button variant="ghost" size="md" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            variant="danger"
            size="md"
            onClick={handleSeed}
            isLoading={isLoading}
            leftIcon={<Database className="w-4 h-4" />}
          >
            Confirm & Seed Data
          </Button>
        </div>
      </div>
    </Modal>
  );
};
