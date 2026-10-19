import React, { useState, useEffect, useCallback } from 'react';
import { User, Check, RefreshCw, AlertCircle } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { endpoints, minorToMajor, majorToMinor, ApiError, type UserProfile } from '../../api';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProfileUpdated?: (profile: UserProfile) => void;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  onClose,
  onProfileUpdated,
}) => {
  const [currency, setCurrency] = useState('USD');
  const [timezone, setTimezone] = useState('Asia/Karachi');
  const [monthlyIncomeDollars, setMonthlyIncomeDollars] = useState(0);
  const [openingBalanceDollars, setOpeningBalanceDollars] = useState(0);
  const [safetyBufferDollars, setSafetyBufferDollars] = useState(0);

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    setStatusMessage(null);
    try {
      const response = await endpoints.profile.get();
      const prof = response.result;
      setCurrency(prof.currency || 'USD');
      setTimezone(prof.timezone || 'Asia/Karachi');
      setMonthlyIncomeDollars(minorToMajor(prof.monthly_income_minor));
      setOpeningBalanceDollars(minorToMajor(prof.opening_balance_minor));
      setSafetyBufferDollars(minorToMajor(prof.safety_buffer_minor));
    } catch (err) {
      if (err instanceof ApiError && err.code === 'FIN_PROFILE_NOT_FOUND') {
        setStatusMessage({
          type: 'error',
          text: 'Profile not found on backend. Fill details below and save to initialize your profile.',
        });
      } else {
        // Keep defaults and inform
        setStatusMessage({
          type: 'error',
          text: err instanceof Error ? err.message : 'Could not fetch remote profile.',
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    loadProfile();
  }, [isOpen, loadProfile]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setStatusMessage(null);

    try {
      const payload = {
        currency: currency.toUpperCase().trim(),
        timezone: timezone.trim(),
        monthly_income_minor: majorToMinor(monthlyIncomeDollars),
        opening_balance_minor: majorToMinor(openingBalanceDollars),
        safety_buffer_minor: majorToMinor(safetyBufferDollars),
      };

      const response = await endpoints.profile.update(payload);
      setStatusMessage({
        type: 'success',
        text: 'Financial preferences updated successfully.',
      });
      if (onProfileUpdated) {
        onProfileUpdated(response.result);
      }
      setTimeout(() => {
        onClose();
      }, 900);
    } catch (err) {
      if (err instanceof ApiError) {
        setStatusMessage({
          type: 'error',
          text: `[${err.code}] ${err.message}`,
        });
      } else {
        setStatusMessage({
          type: 'error',
          text: err instanceof Error ? err.message : 'Failed to update preferences.',
        });
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2.5 text-white">
          <User className="w-5 h-5 text-emerald-400" />
          <span>Finance Preferences & Profile</span>
        </div>
      }
      description="Configure baseline monetary limits, timezone, and cashflow buffers"
      maxWidth="lg"
    >
      <form onSubmit={handleSave} className="space-y-4">
        {statusMessage && (
          <div
            className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
              statusMessage.type === 'success'
                ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/15 border border-rose-500/30 text-rose-300'
            }`}
          >
            {statusMessage.type === 'success' ? (
              <Check className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            )}
            <span>{statusMessage.text}</span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Operating Currency (ISO 3-Letter)
            </label>
            <input
              type="text"
              value={currency}
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
              maxLength={3}
              required
              className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-white text-sm font-mono uppercase focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              placeholder="USD"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Timezone
            </label>
            <input
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-white text-sm font-mono focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              placeholder="Asia/Karachi"
            />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3.5">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Monetary Targets (Automated Minor Units Conversion)
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Monthly Income ($)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-slate-500 text-sm">$</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={monthlyIncomeDollars}
                  onChange={(e) => setMonthlyIncomeDollars(parseFloat(e.target.value) || 0)}
                  required
                  className="w-full pl-7 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <span className="text-[10px] text-slate-400 block mt-1 font-mono">
                {majorToMinor(monthlyIncomeDollars).toLocaleString()} minor units
              </span>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Opening Balance ($)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-slate-500 text-sm">$</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={openingBalanceDollars}
                  onChange={(e) => setOpeningBalanceDollars(parseFloat(e.target.value) || 0)}
                  required
                  className="w-full pl-7 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <span className="text-[10px] text-slate-400 block mt-1 font-mono">
                {majorToMinor(openingBalanceDollars).toLocaleString()} minor units
              </span>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Safety Buffer ($)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-slate-500 text-sm">$</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={safetyBufferDollars}
                  onChange={(e) => setSafetyBufferDollars(parseFloat(e.target.value) || 0)}
                  required
                  className="w-full pl-7 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <span className="text-[10px] text-slate-400 block mt-1 font-mono">
                {majorToMinor(safetyBufferDollars).toLocaleString()} minor units
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={loadProfile}
            disabled={isLoading || isSaving}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          >
            Reload
          </Button>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="md"
              onClick={onClose}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isSaving}
              leftIcon={<Check className="w-4 h-4" />}
            >
              Save Preferences
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};
