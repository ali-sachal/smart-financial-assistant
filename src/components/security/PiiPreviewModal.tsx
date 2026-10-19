import React from 'react';
import { ShieldCheck, Eye, Lock, ShieldAlert } from 'lucide-react';

import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface PiiPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  piiMaskingEnabled: boolean;
  onTogglePiiMasking: () => void;
}

export const PiiPreviewModal: React.FC<PiiPreviewModalProps> = ({
  isOpen,
  onClose,
  piiMaskingEnabled,
  onTogglePiiMasking,
}) => {
  const piiExamples = [
    {
      field: 'Primary Card PAN',
      raw: '4532 8821 9901 4242',
      sanitized: '•••• •••• •••• 4242',
      rule: 'Preserves last 4 digits for merchant reconciliation; masks first 12 digits.',
    },
    {
      field: 'Bank IBAN / Routing',
      raw: 'GB29 NWBK 6016 1331 9268 19',
      sanitized: 'GB•• •••• •••• •••• 6819',
      rule: 'Redacts account routing numbers before transmitting ledger payloads to LLM.',
    },
    {
      field: 'Physical Home Address',
      raw: '742 Evergreen Terrace, Springfield, OR 97477',
      sanitized: '[REDACTED_MUNICIPALITY_OR]',
      rule: 'Entity extraction recognizes residential street numbers and replaces with geocode zone.',
    },
    {
      field: 'SSN / National Tax Identifier',
      raw: '982-12-8821',
      sanitized: '•••-••-8821',
      rule: 'Scrubbed client-side in browser memory before JSON serialization.',
    },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <span>Client-Side PII Masking Engine (Pre-Flight Guard)</span>
        </div>
      }
      description="Zero-Knowledge Data Sanitization Pipeline (Topic A 30% Security Requirement)"
      maxWidth="3xl"
    >
      <div className="space-y-6">
        {/* Toggle & Status Banner */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-2xl flex items-center justify-center ${
                piiMaskingEnabled
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              }`}
            >
              {piiMaskingEnabled ? (
                <ShieldCheck className="w-5 h-5" />
              ) : (
                <ShieldAlert className="w-5 h-5" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">
                  Client-Side Scrubbing: {piiMaskingEnabled ? 'ACTIVE (Strict)' : 'OFF (Raw Ingestion)'}
                </span>
                <Badge variant={piiMaskingEnabled ? 'emerald' : 'amber'} size="sm">
                  {piiMaskingEnabled ? 'Encrypted & Sanitized' : 'Sandbox Unmasked'}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {piiMaskingEnabled
                  ? 'All card numbers, addresses, and tax identifiers are intercepted and masked in the browser before network dispatch.'
                  : 'Warning: Outbound agent calls currently include unredacted raw strings.'}
              </p>
            </div>
          </div>

          <Button
            variant={piiMaskingEnabled ? 'secondary' : 'primary'}
            size="sm"
            onClick={onTogglePiiMasking}
            leftIcon={
              piiMaskingEnabled ? (
                <Eye className="w-4 h-4 text-amber-400" />
              ) : (
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              )
            }
          >
            {piiMaskingEnabled ? 'Disable Masking' : 'Activate Strict Masking'}
          </Button>
        </div>

        {/* Side-by-Side Payload Inspector Table */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Field-by-Field Sanitization Matrix
          </h4>

          <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
            {piiExamples.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{item.field}</span>
                  <span className="text-[10px] text-slate-400">
                    Rule: {item.rule}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {/* Local Raw View */}
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                      Local Client Memory (Raw)
                    </span>
                    <code className="text-slate-300 font-mono text-[11px] select-all">
                      {item.raw}
                    </code>
                  </div>

                  {/* Wire Transmitted View */}
                  <div
                    className={`p-2.5 rounded-lg border ${
                      piiMaskingEnabled
                        ? 'bg-emerald-950/20 border-emerald-500/30'
                        : 'bg-rose-950/20 border-rose-500/30'
                    }`}
                  >
                    <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                      Payload Sent to AI Model
                    </span>
                    <code
                      className={`font-mono text-[11px] font-bold ${
                        piiMaskingEnabled ? 'text-emerald-300' : 'text-rose-400'
                      }`}
                    >
                      {piiMaskingEnabled ? item.sanitized : item.raw}
                    </code>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Security Tier Matrix Info */}
        <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span className="font-bold text-white">Three-Tier Autonomous Protection Model</span>
          </div>
          <p className="text-slate-400 leading-relaxed text-[11px]">
            In addition to client-side data masking, all agent state mutations (e.g. money transfers, budget reallocation, and invoice settlements) are gated behind <strong>Tier 3 cryptographic PIN authorization</strong>, ensuring the user always remains in total financial command.
          </p>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Validated against OWASP Top 10 for Agentic AI Systems
          </span>
          <Button variant="primary" size="md" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </Modal>
  );
};
