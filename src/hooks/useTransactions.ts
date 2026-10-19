import { useState, useCallback, useMemo, useEffect } from 'react';
import type {
  Transaction,
  CategoryBudget,
  CashflowPoint,
  DeficitWarning,
  ExtractedBill,
  MetricSummary,
} from '../types/financial';
import {
  endpoints,
  minorToMajor,
  majorToMinor,
  type DashboardResult,
} from '../api';

const CATEGORY_META: Record<string, { name: string; icon: string; color: string }> = {
  groceries: { name: 'Groceries & Essentials', icon: 'ShoppingCart', color: '#10b981' },
  dining: { name: 'Dining & Social', icon: 'Utensils', color: '#f43f5e' },
  subscriptions: { name: 'Cloud & Subscriptions', icon: 'Cloud', color: '#8b5cf6' },
  cloud: { name: 'Cloud & Subscriptions', icon: 'Cloud', color: '#8b5cf6' },
  entertainment: { name: 'Entertainment & Leisure', icon: 'Film', color: '#06b6d4' },
  utilities: { name: 'Utilities & Internet', icon: 'Zap', color: '#f59e0b' },
  transportation: { name: 'Transportation & Commute', icon: 'Car', color: '#3b82f6' },
  transport: { name: 'Transportation & Commute', icon: 'Car', color: '#3b82f6' },
  wellness: { name: 'Health & Wellness', icon: 'HeartPulse', color: '#14b8a6' },
  healthcare: { name: 'Health & Wellness', icon: 'HeartPulse', color: '#14b8a6' },
  housing: { name: 'Housing & Rent', icon: 'Home', color: '#6366f1' },
  savings: { name: 'Savings & Reserves', icon: 'PiggyBank', color: '#059669' },
};

function getCategoryMeta(cat: string) {
  const key = (cat || 'general').toLowerCase().trim();
  if (CATEGORY_META[key]) return CATEGORY_META[key];
  return {
    name: key.charAt(0).toUpperCase() + key.slice(1),
    icon: 'Tag',
    color: '#94a3b8',
  };
}

export function useTransactions() {
  const [categories, setCategories] = useState<CategoryBudget[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [cashflowData, setCashflowData] = useState<CashflowPoint[]>([]);
  const [warnings, setWarnings] = useState<DeficitWarning[]>([]);
  const [bills, setBills] = useState<ExtractedBill[]>([]);
  const [selectedBillId, setSelectedBillId] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [dashboardData, setDashboardData] = useState<DashboardResult | null>(null);

  const selectedBill = useMemo(() => {
    return bills.find((b) => b.id === selectedBillId) || bills[0] || null;
  }, [bills, selectedBillId]);

  // Synchronize state from live backend APIs
  const refreshData = useCallback(async () => {
    setIsLoading(true);
    try {
      // 1. Fetch dashboard aggregated metrics
      const dashRes = await endpoints.dashboard.get().catch(() => null);
      if (dashRes?.result) {
        const d = dashRes.result;
        setDashboardData(d);

        // Map real budgets
        if (d.budgets && d.budgets.length > 0) {
          const mappedCats: CategoryBudget[] = d.budgets.map((b) => {
            const meta = getCategoryMeta(b.category);
            const spent = minorToMajor(b.spent_minor);
            const allocated = minorToMajor(b.limit_minor);
            return {
              id: `cat-${b.category}`,
              name: meta.name,
              icon: meta.icon,
              allocated,
              spent,
              aiSuggested: allocated,
              velocity: b.utilization || 0,
              period: 'monthly',
              color: meta.color,
              isAlert: (b.utilization || 0) > 0.9,
            };
          });
          setCategories(mappedCats);
        } else if (d.summary?.category_totals && Object.keys(d.summary.category_totals).length > 0) {
          const mappedCats: CategoryBudget[] = Object.entries(d.summary.category_totals).map(
            ([catKey, spentMinor]) => {
              const meta = getCategoryMeta(catKey);
              const spent = minorToMajor(spentMinor);
              return {
                id: `cat-${catKey}`,
                name: meta.name,
                icon: meta.icon,
                allocated: spent || 100,
                spent,
                aiSuggested: spent || 100,
                velocity: 1.0,
                period: 'monthly',
                color: meta.color,
                isAlert: false,
              };
            }
          );
          setCategories(mappedCats);
        } else {
          setCategories([]);
        }

        // Map cashflow forecast points
        if (d.forecast?.points && d.forecast.points.length > 0) {
          const mappedPoints: CashflowPoint[] = d.forecast.points.map((pt) => ({
            date: pt.date,
            dayLabel: pt.date.slice(5),
            income: minorToMajor(pt.scheduled_income_minor),
            expense: minorToMajor(pt.scheduled_expense_minor),
            netBalance: minorToMajor(pt.projected_minor),
            projectedBalance: minorToMajor(pt.projected_minor),
            burnRateUpper: minorToMajor(pt.upper_minor),
            burnRateLower: minorToMajor(pt.lower_minor),
            isProjected: true,
          }));
          setCashflowData(mappedPoints);
        } else {
          setCashflowData([]);
        }

        // Map backend insights into alerts
        if (d.insights && d.insights.length > 0) {
          const mappedWarnings: DeficitWarning[] = d.insights.map((ins, i) => ({
            id: `warn-${i}`,
            severity: ins.type === 'budget_exceeded' ? 'danger' : 'warning',
            title: ins.message || `Alert: ${ins.type}`,
            message: ins.message || `Anomaly flagged in ${ins.category || 'spending'}.`,
            category: ins.category ? getCategoryMeta(ins.category).name : 'General',
            projectedDeficitDate: ins.date || 'Active Month',
            recommendedAction:
              ins.type === 'budget_exceeded'
                ? 'Reallocate budget buffer to prevent overdraft'
                : 'Monitor spending acceleration',
            potentialImpact: ins.amount_minor ? minorToMajor(ins.amount_minor) : 0,
          }));
          setWarnings(mappedWarnings);
        } else {
          setWarnings([]);
        }
      }

      // 2. Fetch live transactions
      const txnRes = await endpoints.transactions.list({ limit: 100 }).catch(() => null);
      if (txnRes?.result?.items) {
        const mappedTxns: Transaction[] = txnRes.result.items.map((t) => ({
          id: t.transaction_id,
          date: t.posted_at,
          merchant: t.merchant,
          category: getCategoryMeta(t.category).name,
          amount: minorToMajor(t.amount_minor),
          type: (t.transaction_type as any) || 'expense',
          status: 'settled',
          paymentMethod: t.account_id || 'Checking Account',
          notes: t.notes || '',
        }));
        setTransactions(mappedTxns);
      } else {
        setTransactions([]);
      }

      // 3. Fetch scheduled bills
      const billsRes = await endpoints.bills.list(30).catch(() => null);
      if (billsRes?.result && billsRes.result.length > 0) {
        const mappedBills: ExtractedBill[] = billsRes.result.map((b) => ({
          id: b.bill_id,
          fileName: `${b.name}.pdf`,
          fileType: 'pdf',
          fileSize: '—',
          uploadTime: b.created_at ? new Date(b.created_at).toLocaleDateString() : 'Active',
          merchant: b.name,
          invoiceDate: b.next_due_date,
          invoiceNumber: b.bill_id.slice(0, 8),
          subtotal: minorToMajor(b.amount_minor),
          taxRate: 0,
          taxAmount: 0,
          totalAmount: minorToMajor(b.amount_minor),
          status: b.active ? 'verified' : 'extracted',
          confidenceScore: 1.0,
          piiDetected: false,
          rawPii: { cardPan: '', address: '' },
          maskedPii: { cardPan: '', address: '' },
          items: [
            {
              id: `item-${b.bill_id}`,
              description: `${b.name} (${b.frequency})`,
              quantity: 1,
              unitPrice: minorToMajor(b.amount_minor),
              amount: minorToMajor(b.amount_minor),
              category: getCategoryMeta(b.category).name,
              confidence: 1.0,
            },
          ],
        }));
        setBills(mappedBills);
        setSelectedBillId(mappedBills[0].id);
      } else {
        setBills([]);
        setSelectedBillId('');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Derived Financial Metrics purely computed from real live state
  const metrics: MetricSummary = useMemo(() => {
    const totalInflow = dashboardData?.summary?.income_minor
      ? minorToMajor(dashboardData.summary.income_minor)
      : transactions.filter((t) => t.type === 'income').reduce((s, t) => s + t.amount, 0);

    const discretionaryOutflow = dashboardData?.summary?.spending_minor
      ? minorToMajor(dashboardData.summary.spending_minor)
      : categories.reduce((sum, cat) => sum + cat.spent, 0);

    const fixedOutflow = bills.reduce((s, b) => s + b.totalAmount, 0);
    const totalOutflow = discretionaryOutflow + fixedOutflow;
    const netSavings = totalInflow - totalOutflow;
    const savingsRate = totalInflow > 0 ? Math.round((netSavings / totalInflow) * 100) : 0;
    const currentDay = Math.max(1, new Date().getDate());
    const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
    const remainingDays = Math.max(1, daysInMonth - currentDay);
    const dailyBurnRate = Number((discretionaryOutflow / currentDay).toFixed(2));
    const totalBalance = dashboardData?.balance?.balance_minor
      ? minorToMajor(dashboardData.balance.balance_minor)
      : 0;
    const runwayDays =
      dailyBurnRate > 0
        ? Math.round(totalBalance / dailyBurnRate)
        : totalBalance > 0
        ? 999
        : 0;
    const totalAllocated = categories.reduce((s, c) => s + c.allocated, 0);
    const safeToSpendDaily = Number(
      ((totalAllocated - discretionaryOutflow) / remainingDays).toFixed(2)
    );

    let healthScore = 80;
    if (savingsRate > 25) healthScore += 10;
    else if (savingsRate < 0) healthScore -= 20;
    if (warnings.some((w) => w.severity === 'danger')) healthScore -= 15;

    return {
      totalInflow,
      fixedOutflow,
      discretionaryOutflow,
      netSavings,
      savingsRate,
      dailyBurnRate,
      runwayDays,
      healthScore: Math.max(10, Math.min(100, healthScore)),
      scoreChange: 0,
      safeToSpendDaily: Math.max(0, safeToSpendDaily),
    };
  }, [dashboardData, transactions, categories, bills, warnings]);

  // Budget Reallocation Action
  const reallocateBudget = useCallback((fromId: string, toId: string, amount: number) => {
    setCategories((prev) =>
      prev.map((cat) => {
        if (cat.id === fromId) {
          return { ...cat, allocated: Math.max(cat.spent, cat.allocated - amount) };
        }
        if (cat.id === toId) {
          const newAllocated = cat.allocated + amount;
          return {
            ...cat,
            allocated: newAllocated,
            isAlert: newAllocated > 0 ? cat.spent / newAllocated > 0.9 : false,
          };
        }
        return cat;
      })
    );
    setWarnings((prev) => prev.filter((w) => !w.id.includes('dining')));
  }, []);

  // Update specific category allocated amount and persist to API
  const updateCategoryAllocation = useCallback((categoryId: string, newAmount: number) => {
    const rawCategory = categoryId.replace(/^cat-/, '');
    const currentMonth = new Date().toISOString().slice(0, 7);
    endpoints.budgets
      .update(currentMonth, rawCategory, { limit_minor: majorToMinor(newAmount) })
      .catch((err: unknown) => console.warn('Failed to update budget on API:', err));

    setCategories((prev) =>
      prev.map((cat) => {
        if (cat.id === categoryId) {
          return {
            ...cat,
            allocated: newAmount,
            isAlert: newAmount > 0 ? cat.spent / newAmount > 0.9 : false,
          };
        }
        return cat;
      })
    );
  }, []);

  // One-click AI Budget Optimization Plan
  const applyAiOptimizationPlan = useCallback(() => {
    setCategories((prev) =>
      prev.map((cat) => ({
        ...cat,
        allocated: cat.aiSuggested,
        isAlert: cat.aiSuggested > 0 ? cat.spent / cat.aiSuggested > 0.9 : false,
      }))
    );
  }, []);

  // Override Line Item Category
  const overrideItemCategory = useCallback((billId: string, itemId: string, newCategory: string) => {
    setBills((prev) =>
      prev.map((b) => {
        if (b.id !== billId) return b;
        return {
          ...b,
          items: b.items.map((item) => {
            if (item.id !== itemId) return item;
            return {
              ...item,
              category: newCategory,
              confidence: 1.0,
            };
          }),
        };
      })
    );
  }, []);

  // Settle or Verify Bill
  const settleBill = useCallback((billId: string) => {
    setBills((prev) =>
      prev.map((b) => (b.id === billId ? { ...b, status: 'verified' } : b))
    );
  }, []);

  // Cancel subscription action
  const cancelSubscription = useCallback((merchant: string) => {
    setTransactions((prev) =>
      prev.filter((t) => !t.merchant.toLowerCase().includes(merchant.toLowerCase()))
    );
  }, []);

  // Transfer funds to emergency fund
  const transferToEmergency = useCallback((amount: number) => {
    const newTx: Transaction = {
      id: `tx-tf-${Date.now()}`,
      date: new Date().toISOString().replace('T', ' ').slice(0, 16),
      merchant: 'Aura High-Yield Treasury Vault',
      category: 'Savings',
      amount: amount,
      type: 'expense',
      status: 'settled',
      paymentMethod: 'Internal Auto-Sweep',
      notes: 'Emergency reserve transfer',
    };
    setTransactions((prev) => [newTx, ...prev]);
  }, []);

  // Handle uploaded new bill from scan
  const uploadNewBill = useCallback((customBill?: Partial<ExtractedBill>) => {
    if (!customBill) return null;
    const newBill: ExtractedBill = {
      id: customBill.id || `bill-${Date.now()}`,
      fileName: customBill.fileName || 'Uploaded_Receipt.pdf',
      fileType: customBill.fileType || 'pdf',
      fileSize: customBill.fileSize || '—',
      uploadTime: 'Just now',
      merchant: customBill.merchant || 'Uploaded Receipt',
      invoiceDate: customBill.invoiceDate || new Date().toISOString().split('T')[0],
      invoiceNumber: customBill.invoiceNumber || `REC-${Date.now().toString().slice(-6)}`,
      subtotal: customBill.subtotal || customBill.totalAmount || 0,
      taxRate: customBill.taxRate || 0,
      taxAmount: customBill.taxAmount || 0,
      totalAmount: customBill.totalAmount || 0,
      status: customBill.status || 'extracted',
      confidenceScore: customBill.confidenceScore ?? 1.0,
      piiDetected: false,
      rawPii: { cardPan: '', address: '' },
      maskedPii: { cardPan: '', address: '' },
      items: customBill.items || [
        {
          id: `item-${Date.now()}`,
          description: customBill.merchant || 'Receipt Item',
          quantity: 1,
          unitPrice: customBill.totalAmount || 0,
          amount: customBill.totalAmount || 0,
          category: 'Groceries & Essentials',
          confidence: 1.0,
        },
      ],
    };

    setBills((prev) => [newBill, ...prev]);
    setSelectedBillId(newBill.id);
    return newBill;
  }, []);

  const dismissWarning = useCallback((warningId: string) => {
    setWarnings((prev) => prev.filter((w) => w.id !== warningId));
  }, []);

  const addTransaction = useCallback((newTxn: Transaction) => {
    setTransactions((prev) => [newTxn, ...prev]);
  }, []);

  return {
    categories,
    transactions,
    setTransactions,
    addTransaction,
    cashflowData,
    warnings,
    bills,
    selectedBill,
    setSelectedBillId,
    metrics,
    reallocateBudget,
    updateCategoryAllocation,
    applyAiOptimizationPlan,
    overrideItemCategory,
    settleBill,
    cancelSubscription,
    transferToEmergency,
    uploadNewBill,
    dismissWarning,
    refreshData,
    isLoading,
  };
}
