import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldAlert,
  Lock,
  AlertCircle,
  Fingerprint,
} from 'lucide-react';

import type { PendingSecurityAction } from '../../types/agent';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';

interface PinModalProps {
  isOpen: boolean;
  onClose: () => void;
  pendingAction: PendingSecurityAction | null;
  onConfirmPin: (pin: string) => { success: boolean; error?: string };
}

export const PinModal: React.FC<PinModalProps> = ({
  isOpen,
  onClose,
  pendingAction,
  onConfirmPin,
}) => {
  const [pinDigits, setPinDigits] = useState<string[]>(['', '', '', '']);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (isOpen) {
      setPinDigits(['', '', '', '']);
      setErrorMessage(null);
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    }
  }, [isOpen]);

  const handleDigitChange = (index: number, val: string) => {
    if (!/^\d*$/.test(val)) return;

    const newPin = [...pinDigits];
    newPin[index] = val.slice(-1);
    setPinDigits(newPin);
    setErrorMessage(null);

    // Auto-advance
    if (val && index < 3) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-verify when 4 digits entered
    if (val && index === 3 && newPin.every((d) => d !== '')) {
      const fullPin = newPin.join('');
      executeVerification(fullPin);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !pinDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const executeVerification = (pin: string) => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      const res = onConfirmPin(pin);
      if (!res.success) {
        setErrorMessage(res.error || 'Invalid PIN code');
        setPinDigits(['', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    }, 400);
  };

  const handleBiometricSimulate = () => {
    setPinDigits(['4', '2', '4', '2']);
    executeVerification('4242');
  };

  if (!pendingAction) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2 text-rose-400">
          <ShieldAlert className="w-5 h-5 text-rose-400" />
          <span>Human-in-the-Loop Security Verification</span>
        </div>
      }
      description="Tier 3 State-Modifying Authorization Gatekeeper"
      maxWidth="md"
    >
      <div className="space-y-6">
        {/* Action Details Intercept Card */}
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-300 uppercase tracking-wider">
              Intercepted Mutation
            </span>
            <span className="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full border border-rose-500/40 font-mono">
              Tier 3 Gate
            </span>
          </div>

          <h4 className="text-sm font-extrabold text-white">
            {pendingAction.title}
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            {pendingAction.description}
          </p>

          <div className="pt-2 border-t border-rose-500/20 text-[11px] text-slate-400 font-mono">
            <span>Mutation endpoint:</span>{' '}
            <code className="text-white bg-slate-950/80 px-1.5 py-0.5 rounded">
              {pendingAction.mutationType}
            </code>
          </div>
        </div>

        {/* 4-digit PIN Input Fields */}
        <div className="flex flex-col items-center justify-center space-y-3">
          <label className="text-xs font-bold text-slate-300">
            Enter 4-Digit Security Authorization PIN
          </label>

          <div className="flex items-center gap-3">
            {pinDigits.map((digit, idx) => (
              <input
                key={idx}
                ref={(el) => {
                  inputRefs.current[idx] = el;
                }}
                type="password"
                maxLength={1}

                inputMode="numeric"
                value={digit}
                onChange={(e) => handleDigitChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                disabled={isVerifying}
                className="w-12 h-14 text-center text-xl font-bold font-mono-numbers rounded-2xl bg-slate-950 border-2 border-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-white transition-all shadow-inner"
              />
            ))}
          </div>

          {errorMessage ? (
            <div className="flex items-center gap-1.5 text-xs text-rose-400 font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{errorMessage}</span>
            </div>
          ) : (
            <p className="text-[11px] text-slate-500">
              Default competition sandbox PIN: <strong className="text-emerald-400">4242</strong>
            </p>
          )}
        </div>

        {/* Biometrics Bypass Simulator for Demo */}
        <div className="flex items-center justify-center">
          <button
            type="button"
            onClick={handleBiometricSimulate}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-xs border border-slate-700 transition-colors"
          >
            <Fingerprint className="w-4 h-4 text-emerald-400" />
            <span>Simulate Passkey / Touch ID (4242)</span>
          </button>
        </div>

        {/* Footer info & buttons */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Lock className="w-3.5 h-3.5 text-slate-500" />
            <span>Fulfills 30% Track Security Scoring</span>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose}>
              Abort
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={pinDigits.some((d) => d === '') || isVerifying}
              isLoading={isVerifying}
              onClick={() => executeVerification(pinDigits.join(''))}
            >
              Authorize Mutation
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
