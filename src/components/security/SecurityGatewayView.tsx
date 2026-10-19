import React from 'react';
import {
  ShieldCheck,
  Lock,
  KeyRound,
  Eye,
  EyeOff,
  Check,
  Terminal,
} from 'lucide-react';

import type { SecurityTier, SecurityTierInfo } from '../../types/agent';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface SecurityGatewayViewProps {
  currentTier: SecurityTier;
  setCurrentTier: (tier: SecurityTier) => void;
  tierConfigs: Record<SecurityTier, SecurityTierInfo>;
  piiMaskingEnabled: boolean;
  onTogglePiiMasking: () => void;
  onOpenPiiModal: () => void;
  onOpenAuditDrawer: () => void;
  auditCount: number;
}

export const SecurityGatewayView: React.FC<SecurityGatewayViewProps> = ({
  currentTier,
  setCurrentTier,
  tierConfigs,
  piiMaskingEnabled,
  onTogglePiiMasking,
  onOpenPiiModal,
  onOpenAuditDrawer,
  auditCount,
}) => {
  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <Card className="p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-tight m-0">
                  Security & Permission-Tier Gateway
                </h2>
                <Badge variant="emerald" size="sm">
                  30% Track Evaluation
                </Badge>
              </div>
              <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
                Operating under the <strong>AI as a Financial Participant</strong> standard. The system guarantees that autonomous agents can never execute state mutations or leak raw sensitive credentials without explicit client-side sanitization and cryptographic PIN verification.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenPiiModal}
              leftIcon={<Eye className="w-4 h-4 text-emerald-400" />}
            >
              Inspect PII Masking
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={onOpenAuditDrawer}
              leftIcon={<Terminal className="w-4 h-4 text-sky-400" />}
            >
              Execution Evidence ({auditCount})
            </Button>
          </div>
        </div>
      </Card>

      {/* Three Permission Tiers Matrix */}
      <div>
        <div className="mb-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
            Operational Autonomy Tiers
          </h3>
          <p className="text-xs text-slate-400">
            Select an operational tier to constrain or elevate the agent's decision boundaries.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {([1, 2, 3] as SecurityTier[]).map((t) => {
            const config = tierConfigs[t];
            const isSelected = currentTier === t;

            return (
              <Card
                key={t}
                className={`p-5 flex flex-col justify-between transition-all duration-300 border-2 ${
                  isSelected
                    ? t === 3
                      ? 'border-emerald-500 bg-emerald-950/20 shadow-xl shadow-emerald-500/10'
                      : t === 2
                      ? 'border-amber-500 bg-amber-950/20 shadow-xl shadow-amber-500/10'
                      : 'border-slate-500 bg-slate-900/60'
                    : 'border-slate-800/80 hover:border-slate-700 bg-slate-950/60'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                      Tier 0{t} Architecture
                    </span>
                    {isSelected && (
                      <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full border border-emerald-500/40">
                        <Check className="w-3.5 h-3.5" /> Active Tier
                      </span>
                    )}
                  </div>

                  <h4 className="text-base font-bold text-white tracking-tight">
                    {config.name}
                  </h4>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                    {config.description}
                  </p>

                  {/* Capabilities List */}
                  <div className="mt-4 space-y-2 border-t border-slate-800/80 pt-3">
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">
                      Permitted Functions:
                    </span>
                    {config.allowedActions.map((action, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
                        <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>{action}</span>
                      </div>
                    ))}

                    {config.restrictedActions.length > 0 && (
                      <>
                        <span className="text-[10px] font-bold uppercase text-slate-500 block pt-2">
                          Restricted Functions:
                        </span>
                        {config.restrictedActions.map((action, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs text-slate-500">
                            <Lock className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                            <span>{action}</span>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-800/80">
                  {config.requiresPin && (
                    <div className="flex items-center gap-1.5 text-[11px] text-amber-400 font-medium mb-3">
                      <KeyRound className="w-3.5 h-3.5" />
                      <span>Demands 4-Digit PIN Authentication</span>
                    </div>
                  )}

                  <Button
                    variant={isSelected ? 'secondary' : 'outline'}
                    size="sm"
                    className="w-full"
                    onClick={() => setCurrentTier(t)}
                  >
                    {isSelected ? 'Currently Selected' : `Switch to Tier ${t}`}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* PII Scrubbing Demonstration Card */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                Client-Side PII Scrubbing Layer
              </h3>
              <Badge variant={piiMaskingEnabled ? 'emerald' : 'amber'} size="sm">
                {piiMaskingEnabled ? 'Sanitization Active' : 'Unmasked'}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Zero-knowledge client pipeline transforms credentials before JSON transmission to models.
            </p>
          </div>

          <Button
            variant={piiMaskingEnabled ? 'secondary' : 'primary'}
            size="sm"
            onClick={onTogglePiiMasking}
            leftIcon={
              piiMaskingEnabled ? (
                <EyeOff className="w-4 h-4 text-emerald-400" />
              ) : (
                <Eye className="w-4 h-4 text-amber-400" />
              )
            }
          >
            {piiMaskingEnabled ? 'Deactivate Sanitizer' : 'Activate Sanitizer'}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">Card PAN Mask</span>
            <p className="font-mono text-emerald-300 font-bold">4532 •••• •••• 4242</p>
            <p className="text-[11px] text-slate-400">Scrubbed locally in browser heap</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">IBAN Routing Mask</span>
            <p className="font-mono text-emerald-300 font-bold">GB•• •••• •••• •••• 6819</p>
            <p className="text-[11px] text-slate-400">Redacted before vision OCR call</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">Address Entity Sanitization</span>
            <p className="font-mono text-emerald-300 font-bold">[REDACTED_MUNICIPALITY_OR]</p>
            <p className="text-[11px] text-slate-400">Residential coordinates filtered</p>
          </div>
        </div>
      </Card>
    </div>
  );
};
