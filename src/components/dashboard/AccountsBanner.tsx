import React from 'react';
import { CreditCard, Plus, RefreshCw, Database } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { formatCurrencyMinor, type AccountItem } from '../../api';

interface AccountsBannerProps {
  accounts: AccountItem[];
  isLoading: boolean;
  onRefresh: () => void;
  onOpenNewTransaction: () => void;
  onOpenSeedModal: () => void;
  lastSynced?: Date | null;
}

export const AccountsBanner: React.FC<AccountsBannerProps> = ({
  accounts,
  isLoading,
  onRefresh,
  onOpenNewTransaction,
  onOpenSeedModal,
  lastSynced,
}) => {
  return (
    <Card className="p-4 sm:p-5 bg-gradient-to-r from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Left: Accounts balance list */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shadow-inner">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Primary Liquidity Vault
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold text-white font-mono-numbers">
                  {accounts.length > 0
                    ? formatCurrencyMinor(
                        accounts.reduce((sum, a) => sum + (a.balance_minor || 0), 0),
                        accounts[0]?.currency || 'USD'
                      )
                    : '$0.00'}
                </span>
                <Badge variant="emerald" size="sm">
                  Active
                </Badge>
              </div>
            </div>
          </div>

          {/* Sub-accounts badges */}
          <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-slate-800">
            {accounts.map((acc) => (
              <div
                key={acc.account_id}
                className="px-3 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs flex items-center gap-2"
              >
                <span className="text-slate-400">{acc.name}:</span>
                <span className="font-semibold text-slate-200 font-mono-numbers">
                  {formatCurrencyMinor(acc.balance_minor, acc.currency)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Quick actions */}
        <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            title={lastSynced ? `Last synced: ${lastSynced.toLocaleTimeString()}` : 'Sync with API'}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />}
          >
            <span className="hidden md:inline">Sync</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenSeedModal}
            leftIcon={<Database className="w-3.5 h-3.5 text-amber-400" />}
            title="Seed demo dataset into user partition"
          >
            <span className="hidden md:inline">Seed Demo</span>
          </Button>

          <Button
            variant="glow"
            size="sm"
            onClick={onOpenNewTransaction}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Txn
          </Button>
        </div>
      </div>
    </Card>
  );
};
