import React, { useState } from 'react';
import { Plus, Check, AlertCircle } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { endpoints, majorToMinor, ApiError, type ApiTransactionItem, type ApiTransactionType } from '../../api';

interface NewTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTransactionCreated?: (transaction: ApiTransactionItem) => void;
}

const CATEGORIES = [
  'groceries',
  'dining',
  'utilities',
  'housing',
  'transportation',
  'subscriptions',
  'entertainment',
  'healthcare',
  'income',
  'other',
];

export const NewTransactionModal: React.FC<NewTransactionModalProps> = ({
  isOpen,
  onClose,
  onTransactionCreated,
}) => {
  const [merchant, setMerchant] = useState('');
  const [category, setCategory] = useState('groceries');
  const [amountDollars, setAmountDollars] = useState<string>('');
  const [transactionType, setTransactionType] = useState<ApiTransactionType>('expense');
  const [postedAt, setPostedAt] = useState(() => new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const parsedAmount = parseFloat(amountDollars);
    if (!parsedAmount || parsedAmount <= 0) {
      setError('Amount must be greater than zero.');
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        account_id: 'checking',
        amount_minor: majorToMinor(parsedAmount),
        currency: 'USD',
        transaction_type: transactionType,
        category: category.toLowerCase().trim(),
        merchant: merchant.trim(),
        posted_at: postedAt,
        source: 'manual' as const,
        notes: notes.trim() || undefined,
      };

      const res = await endpoints.transactions.create(payload);
      if (onTransactionCreated) {
        onTransactionCreated(res.result);
      }
      setMerchant('');
      setNotes('');
      setAmountDollars('');
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`[${err.code}] ${err.message}`);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to record transaction.');
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
        <div className="flex items-center gap-2 text-white">
          <Plus className="w-5 h-5 text-emerald-400" />
          <span>Record New Transaction</span>
        </div>
      }
      description="Dispatches to POST /transactions with integer minor units"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-2 bg-slate-950/70 p-1 rounded-xl border border-slate-800">
          <button
            type="button"
            onClick={() => setTransactionType('expense')}
            className={`py-2 rounded-lg text-xs font-semibold transition-all ${
              transactionType === 'expense'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Expense
          </button>
          <button
            type="button"
            onClick={() => setTransactionType('income')}
            className={`py-2 rounded-lg text-xs font-semibold transition-all ${
              transactionType === 'income'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Income
          </button>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Merchant / Payee
          </label>
          <input
            type="text"
            required
            value={merchant}
            onChange={(e) => setMerchant(e.target.value)}
            placeholder="e.g. Fresh Market, Corner Cafe, Payroll"
            className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Amount ($ USD)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-slate-500 text-sm">$</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={amountDollars}
                onChange={(e) => setAmountDollars(e.target.value)}
                placeholder="0.00"
                className="w-full pl-7 pr-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
            {amountDollars && (
              <span className="text-[10px] text-slate-400 block mt-1 font-mono">
                = {majorToMinor(parseFloat(amountDollars) || 0).toLocaleString()} minor units
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm capitalize focus:outline-none focus:border-emerald-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Date (YYYY-MM-DD)
            </label>
            <input
              type="date"
              required
              value={postedAt}
              onChange={(e) => setPostedAt(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Account
            </label>
            <input
              type="text"
              disabled
              value="checking (Default)"
              className="w-full px-3 py-2 bg-slate-950/50 border border-slate-800 rounded-xl text-slate-400 text-sm font-mono cursor-not-allowed"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Notes / Memo (Optional)
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Weekly grocery trip"
            className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
          <Button type="button" variant="ghost" size="md" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            leftIcon={<Check className="w-4 h-4" />}
          >
            Create Transaction
          </Button>
        </div>
      </form>
    </Modal>
  );
};
