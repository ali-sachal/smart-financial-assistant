import React, { useState } from 'react';
import {
  Calendar,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Building,
} from 'lucide-react';
import type { ExtractedBill } from '../../types/financial';

import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface LineItemGridProps {
  bill: ExtractedBill;
  piiMaskingEnabled: boolean;
  onOverrideCategory: (billId: string, itemId: string, newCategory: string) => void;
  onSettleBill: (billId: string) => void;
}

const CATEGORY_OPTIONS = [
  'Groceries & Essentials',
  'Dining & Social',
  'Cloud & Subscriptions',
  'Entertainment & Leisure',
  'Utilities & Internet',
  'Transportation & Commute',
  'Health & Wellness',
  'General Overhead',
];

export const LineItemGrid: React.FC<LineItemGridProps> = ({
  bill,
  piiMaskingEnabled,
  onOverrideCategory,
  onSettleBill,
}) => {
  const [editingItemId, setEditingItemId] = useState<string | null>(null);

  const getConfidenceBadge = (confidence: number) => {
    const percent = Math.round(confidence * 100);
    if (percent >= 95) {
      return (
        <Badge variant="emerald" size="sm" dot>
          {percent}% High
        </Badge>
      );
    }
    if (percent >= 80) {
      return (
        <Badge variant="amber" size="sm" dot>
          {percent}% Med
        </Badge>
      );
    }
    return (
      <Badge variant="rose" size="sm" dot>
        {percent}% Review
      </Badge>
    );
  };

  if (!bill) {
    return (
      <Card className="p-8 text-center text-slate-400 text-xs">
        No bill selected or uploaded. Drag and drop a bill or invoice above to inspect extracted line items.
      </Card>
    );
  }

  return (
    <Card className="p-6">
      {/* Bill Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-emerald-400">
              <Building className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  {bill.merchant}
                </h3>
                {bill.status === 'verified' ? (
                  <Badge variant="emerald" size="sm">
                    Verified in Ledger
                  </Badge>
                ) : (
                  <Badge variant="sky" size="sm">
                    Extracted via OCR
                  </Badge>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                <span>Invoice #{bill.invoiceNumber}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-500" />
                  {bill.invoiceDate}
                </span>
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">
              Total Invoiced
            </span>
            <p className="text-lg font-extrabold text-white font-mono-numbers">
              ${bill.totalAmount.toFixed(2)}
            </p>
          </div>
          <Button
            variant={bill.status === 'verified' ? 'secondary' : 'primary'}
            size="sm"
            onClick={() => onSettleBill(bill.id)}
            disabled={bill.status === 'verified'}
            leftIcon={<CheckCircle2 className="w-4 h-4 text-emerald-400" />}
          >
            {bill.status === 'verified' ? 'Reconciled' : 'Reconcile & Settle'}
          </Button>
        </div>
      </div>

      {/* PII Sanitization Preview Snippet for this Bill (if present) */}
      {(bill.rawPii?.cardPan || bill.maskedPii?.cardPan || bill.rawPii?.address) && (
        <div className="my-4 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-slate-300 font-semibold">Sanitized Ingestion Metadata:</span>
            {(bill.maskedPii?.cardPan || bill.rawPii?.cardPan) && (
              <>
                <span className="text-slate-400">Payment PAN:</span>
                <code className="text-emerald-300 bg-slate-950 px-2 py-0.5 rounded font-mono text-[11px] border border-slate-800">
                  {piiMaskingEnabled ? bill.maskedPii?.cardPan : bill.rawPii?.cardPan}
                </code>
              </>
            )}
            {bill.rawPii?.address && (
              <>
                <span className="text-slate-400">Address:</span>
                <code className="text-emerald-300 bg-slate-950 px-2 py-0.5 rounded font-mono text-[11px] border border-slate-800">
                  {piiMaskingEnabled ? bill.maskedPii?.address : bill.rawPii?.address}
                </code>
              </>
            )}
          </div>
          <span className="text-[11px] text-slate-400">
            Scrubbed locally before vision payload transmission
          </span>
        </div>
      )}

      {/* Line Items Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <th className="py-3 px-3">Line Item Description</th>
              <th className="py-3 px-3 text-center">Qty</th>
              <th className="py-3 px-3 text-right">Unit Price</th>
              <th className="py-3 px-3 text-right">Amount</th>
              <th className="py-3 px-3">AI Categorization</th>
              <th className="py-3 px-3 text-center">Confidence</th>
              <th className="py-3 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {(!bill.items || bill.items.length === 0) ? (
              <tr>
                <td colSpan={7} className="py-6 text-center text-slate-400">
                  No line items extracted.
                </td>
              </tr>
            ) : (
              bill.items.map((item) => (
              <tr
                key={item.id}
                className="hover:bg-slate-900/50 transition-colors group"
              >
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{item.description}</span>
                    {item.isAnomaly && (
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> Anomalous
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-3 px-3 text-center text-slate-300 font-mono-numbers">
                  {item.quantity}
                </td>
                <td className="py-3 px-3 text-right text-slate-300 font-mono-numbers">
                  ${item.unitPrice.toFixed(2)}
                </td>
                <td className="py-3 px-3 text-right font-bold text-white font-mono-numbers">
                  ${item.amount.toFixed(2)}
                </td>
                <td className="py-3 px-3">
                  {editingItemId === item.id ? (
                    <select
                      value={item.category}
                      onChange={(e) => {
                        onOverrideCategory(bill.id, item.id, e.target.value);
                        setEditingItemId(null);
                      }}
                      className="bg-slate-950 border border-emerald-500 text-white text-xs rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-400"
                    >
                      {CATEGORY_OPTIONS.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded-lg border border-slate-700/60">
                      {item.category}
                    </span>
                  )}
                </td>
                <td className="py-3 px-3 text-center">
                  {getConfidenceBadge(item.confidence)}
                </td>
                <td className="py-3 px-3 text-right">
                  <button
                    onClick={() =>
                      setEditingItemId(editingItemId === item.id ? null : item.id)
                    }
                    className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold transition-colors"
                  >
                    {editingItemId === item.id ? 'Cancel' : 'Override'}
                  </button>
                </td>
              </tr>
            )))}
          </tbody>
        </table>
      </div>

      {/* Invoice Totals Summary Footer */}
      <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-4 text-slate-400">
          <span>
            Subtotal: <strong className="text-white font-mono-numbers">${bill.subtotal.toFixed(2)}</strong>
          </span>
          <span>•</span>
          <span>
            Tax ({(bill.taxRate * 100).toFixed(2)}%): <strong className="text-white font-mono-numbers">${bill.taxAmount.toFixed(2)}</strong>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400">OCR Extraction Quality:</span>
          <Badge variant="emerald" size="sm">
            {(bill.confidenceScore * 100).toFixed(0)}% High Precision
          </Badge>
        </div>
      </div>
    </Card>
  );
};
