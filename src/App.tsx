import { useState, useEffect, useCallback } from 'react';
import confetti from 'canvas-confetti';
import {
  TopNavbar,
  type NavTab,
} from './components/layout/TopNavbar';
import { MetricCards } from './components/dashboard/MetricCards';
import { DailyExpensePie } from './components/dashboard/DailyExpensePie';
import { VelocityTracker } from './components/dashboard/VelocityTracker';
import { CashflowChart } from './components/dashboard/CashflowChart';
import { CategoryList } from './components/dashboard/CategoryList';
import { DeficitAlerts } from './components/dashboard/DeficitAlerts';
import { BudgetSlidersModal } from './components/dashboard/BudgetSlidersModal';
import { AccountsBanner } from './components/dashboard/AccountsBanner';
import { BillUploader } from './components/bills/BillUploader';
import { LineItemGrid } from './components/bills/LineItemGrid';
import { ScheduledBillsSection } from './components/bills/ScheduledBillsSection';
import { SpendingAnalytics } from './components/analytics/SpendingAnalytics';
import { ChatDrawer } from './components/copilot/ChatDrawer';
import { PinModal } from './components/security/PinModal';
import { AuditDrawer } from './components/security/AuditDrawer';
import { PiiPreviewModal } from './components/security/PiiPreviewModal';
import { SecurityGatewayView } from './components/security/SecurityGatewayView';
import { DemoSeedModal } from './components/modals/DemoSeedModal';
import { ProfileModal } from './components/modals/ProfileModal';
import { NewTransactionModal } from './components/modals/NewTransactionModal';

import { useSecurityTier } from './hooks/useSecurityTier';
import { useTransactions } from './hooks/useTransactions';
import { useFinCopilot } from './hooks/useFinCopilot';
import type { ActionRecommendation } from './types/agent';
import type { DeficitWarning } from './types/financial';
import {
  endpoints,
  minorToMajor,
  majorToMinor,
  type AccountItem,
  type ApiTransactionItem,
  type UserProfile,
} from './api';

const INITIAL_ACCOUNTS: AccountItem[] = [];


export function App({ username }: { username?: string } = {}) {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [isSlidersModalOpen, setIsSlidersModalOpen] = useState(false);
  const [isSeedModalOpen, setIsSeedModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isNewTxnModalOpen, setIsNewTxnModalOpen] = useState(false);

  // Accounts state & sync
  const [accounts, setAccounts] = useState<AccountItem[]>(INITIAL_ACCOUNTS);
  const [isAccountsLoading, setIsAccountsLoading] = useState(false);
  const [lastSynced, setLastSynced] = useState<Date | null>(null);

  // Security Tier & Audit Gatekeeper Hook
  const {
    currentTier,
    setCurrentTier,
    activeTierInfo,
    tierConfigs,
    piiMaskingEnabled,
    setPiiMaskingEnabled,
    auditLogs,
    addAuditLog,
    executeGuardedAction,
    pendingAction,
    isPinModalOpen,
    confirmPinAndExecute,
    cancelPendingAction,
    isAuditDrawerOpen,
    setIsAuditDrawerOpen,
    isPiiModalOpen,
    setIsPiiModalOpen,
    exportAuditLogs,
  } = useSecurityTier();

  // Transactions, Categories, and Financial Models Hook
  const {
    categories,
    transactions,
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
  } = useTransactions();

  // Fetch accounts from GET /accounts
  const refreshAccounts = useCallback(async () => {
    setIsAccountsLoading(true);
    try {
      const res = await endpoints.accounts.list();
      setAccounts(res.result || []);
      setLastSynced(new Date());
    } catch {
      // Keep existing accounts
    } finally {
      setIsAccountsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAccounts();
  }, [refreshAccounts]);

  // Handler for Executing AI Recommendations through Security Gatekeeper
  const handleExecuteRecommendation = (rec: ActionRecommendation) => {
    executeGuardedAction({
      title: rec.title,
      description: rec.description,
      tierRequired: rec.tier,
      mutationType: rec.type,
      payload: {
        recommendation_id: rec.id,
        amount: rec.amount,
        from_category: rec.fromCategory,
        to_category: rec.toCategory,
        target_merchant: rec.targetMerchant,
      },
      onExecute: () => {
        if (rec.type === 'budget_reallocate' && rec.fromCategory && rec.toCategory && rec.amount) {
          reallocateBudget(rec.fromCategory, rec.toCategory, rec.amount);
        } else if (rec.type === 'cancel_subscription' && rec.targetMerchant) {
          cancelSubscription(rec.targetMerchant);
        } else if (rec.type === 'fund_transfer' && rec.amount) {
          transferToEmergency(rec.amount);
        }

        try {
          confetti({
            particleCount: 50,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#10b981', '#06b6d4', '#6366f1'],
          });
        } catch {
          // ignore in test environments
        }
      },
    });
  };

  // Conversational Advisory Copilot Hook
  const {
    messages,
    isTyping,
    inputValue,
    setInputValue,
    sendMessage,
    executeRecommendation,
  } = useFinCopilot(metrics, handleExecuteRecommendation);

  // Fix Warning Handler
  const handleFixWarning = (warning: DeficitWarning) => {
    if (warning.id === 'warn-01') {
      // Dining overdraft fix -> Reallocate $80 from Entertainment
      executeGuardedAction({
        title: 'Reallocate $80 from Entertainment to Dining',
        description: 'Prevent dining limit overdraft by transferring $80 buffer from surplus Entertainment.',
        tierRequired: 3,
        mutationType: 'budget_reallocate',
        payload: { from: 'cat-entertainment', to: 'cat-dining', amount: 80 },
        onExecute: () => {
          reallocateBudget('cat-entertainment', 'cat-dining', 80);
          confetti({ particleCount: 40, spread: 60, origin: { y: 0.7 } });
        },
      });
    } else if (warning.id === 'warn-02') {
      // Cancel AWS subscription
      executeGuardedAction({
        title: 'Cancel Inactive AWS GPU Node ($68.20/mo)',
        description: 'Terminate idle cloud computing node flagged by multimodal billing inspector.',
        tierRequired: 3,
        mutationType: 'cancel_subscription',
        payload: { merchant: 'Amazon Web Services', monthly_savings: 68.20 },
        onExecute: () => {
          cancelSubscription('Amazon Web Services');
          confetti({ particleCount: 40, spread: 60, origin: { y: 0.7 } });
        },
      });
    } else if (warning.id === 'warn-03') {
      // Emergency Sweep
      executeGuardedAction({
        title: 'Transfer $150 to High-Yield Treasury Vault',
        description: 'Internal sweep into FDIC treasury earning 4.85% APY.',
        tierRequired: 3,
        mutationType: 'fund_transfer',
        payload: { destination: 'Aura High-Yield Treasury Vault', amount: 150 },
        onExecute: () => {
          transferToEmergency(150);
          confetti({ particleCount: 40, spread: 60, origin: { y: 0.7 } });
        },
      });
    }
  };

  // Reconcile and Settle Bill with Security Check
  const handleSettleBillWithSecurity = (billId: string) => {
    const targetBill = bills.find((b) => b.id === billId);
    if (!targetBill) return;

    executeGuardedAction({
      title: `Reconcile & Settle Invoice: ${targetBill.merchant}`,
      description: `Commit $${targetBill.totalAmount.toFixed(2)} to primary ledger and finalize expense recognition.`,
      tierRequired: 3,
      mutationType: 'settle_bill_invoice',
      payload: {
        bill_id: targetBill.id,
        invoice_number: targetBill.invoiceNumber,
        merchant: targetBill.merchant,
        total_amount: targetBill.totalAmount,
      },
      onExecute: () => {
        settleBill(billId);
        confetti({ particleCount: 60, spread: 70, origin: { y: 0.6 } });
      },
    });
  };

  // Apply AI Optimization Plan with Security Gatekeeper
  const handleApplyAiOptimizationWithSecurity = () => {
    executeGuardedAction({
      title: 'Apply Autonomous AI Budget Optimization Plan',
      description: 'Rebalance all 7 category allocations according to machine-learned 90-day velocity targets.',
      tierRequired: 3,
      mutationType: 'apply_ai_budget_plan',
      payload: {
        categories_rebalanced: 7,
        projected_monthly_savings: 340.00,
        dining_buffer_increase: 80,
      },
      onExecute: () => {
        applyAiOptimizationPlan();
        confetti({ particleCount: 60, spread: 80, origin: { y: 0.6 } });
      },
    });
  };

  // Save allocations from sliders
  const handleSaveAllocationsFromSliders = (updated: Record<string, number>) => {
    executeGuardedAction({
      title: 'Update Category Budget Allocations',
      description: 'Commit custom category ceilings adjusted via interactive allocation sliders.',
      tierRequired: 3,
      mutationType: 'update_category_allocations',
      payload: updated,
      onExecute: () => {
        const currentMonth = new Date().toISOString().slice(0, 7);
        Object.entries(updated).forEach(([id, amt]) => {
          updateCategoryAllocation(id, amt);
          const categorySlug = id.replace(/^cat-/, '');
          endpoints.budgets
            .update(currentMonth, categorySlug, {
              limit_minor: majorToMinor(amt),
              currency: 'USD',
            })
            .catch(() => {});
        });
        confetti({ particleCount: 50, spread: 70, origin: { y: 0.6 } });
      },
    });
  };

  // Handle Demo Seed success
  const handleSeedSuccess = (itemCount: number) => {
    confetti({ particleCount: 80, spread: 90, origin: { y: 0.6 } });
    refreshAccounts();
    refreshData();
    addAuditLog({
      type: 'database_read',
      title: `Seeded ${itemCount} Demo Records`,
      tier: 1,
      status: 'success',
      resultSummary: `Executed POST /demo/seed into user partition.`,
      piiMaskedBeforeSend: piiMaskingEnabled,
      latencyMs: 140,
      fullPayload: { seeded: true, itemCount },
    });
  };

  // Handle New Transaction Created
  const handleTransactionCreated = (txn: ApiTransactionItem) => {
    addTransaction({
      id: txn.transaction_id,
      date: txn.posted_at,
      merchant: txn.merchant,
      category: txn.category,
      amount: minorToMajor(txn.amount_minor),
      type: txn.transaction_type === 'income' ? 'income' : 'expense',
      status: 'settled',
      paymentMethod: txn.account_id || 'checking',
      notes: txn.notes || undefined,
    });
    confetti({ particleCount: 50, spread: 70, origin: { y: 0.6 } });
    refreshAccounts();
    refreshData();
    addAuditLog({
      type: 'state_mutation',
      title: `Created Txn: ${txn.merchant}`,
      tier: 2,
      status: 'success',
      toolName: 'create_transaction',
      resultSummary: `Posted ${txn.transaction_type} of $${minorToMajor(txn.amount_minor).toFixed(2)} to ${txn.category}.`,
      piiMaskedBeforeSend: piiMaskingEnabled,
      latencyMs: 85,
      fullPayload: { ...txn },
    });
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Top Navigation Bar */}
      <TopNavbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentTier={currentTier}
        activeTierInfo={activeTierInfo}
        onOpenSeedModal={() => setIsSeedModalOpen(true)}
        onOpenProfileModal={() => setIsProfileModalOpen(true)}
        username={username}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Proactive Deficit Warnings Bar */}
        <DeficitAlerts
          warnings={warnings}
          onDismiss={dismissWarning}
          onTakeAction={handleFixWarning}
        />

        {/* TAB 1: SMART BUDGETING DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Liquidity Accounts & Sync Banner */}
            <AccountsBanner
              accounts={accounts}
              isLoading={isAccountsLoading}
              onRefresh={refreshAccounts}
              onOpenNewTransaction={() => setIsNewTxnModalOpen(true)}
              onOpenSeedModal={() => setIsSeedModalOpen(true)}
              lastSynced={lastSynced}
            />

            {/* Hero: Daily Expense Pie Chart */}
            <DailyExpensePie categories={categories} />

            {/* Velocity Metric Cards */}
            <MetricCards
              metrics={metrics}
              onOptimizeClick={() => setIsSlidersModalOpen(true)}
            />

            {/* Inflow vs Outflow Velocity Tracker */}
            <VelocityTracker
              metrics={metrics}
              onOpenOptimizeModal={() => setIsSlidersModalOpen(true)}
            />

            {/* Burn Rate & Cash Flow Curves */}
            <CashflowChart data={cashflowData} />

            {/* Category Allocation Progress Bars & Ceilings */}
            <CategoryList
              categories={categories}
              onOpenSliders={() => setIsSlidersModalOpen(true)}
              onApplyOptimization={handleApplyAiOptimizationWithSecurity}
            />
          </div>
        )}

        {/* TAB 2: MULTIMODAL BILL & RECEIPT ANALYSIS */}
        {activeTab === 'bills' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <BillUploader
              onUploadSuccess={(billData) => {
                const created = uploadNewBill(billData);
                if (created) {
                  addAuditLog({
                    type: 'tool_call',
                    title: `Ingested ${created.merchant} Receipt`,
                    tier: 2,
                    status: 'success',
                    toolName: 'vision_ocr_extract',
                    resultSummary: `Extracted ${created.items.length} line items with ${(created.confidenceScore * 100).toFixed(0)}% confidence. PII masked.`,
                    piiMaskedBeforeSend: piiMaskingEnabled,
                    latencyMs: 310,
                    fullPayload: {
                      fileName: created.fileName,
                      total: created.totalAmount,
                      piiSanitized: piiMaskingEnabled,
                    },
                  });
                }
              }}
              piiMaskingEnabled={piiMaskingEnabled}
              selectedBill={selectedBill}
              bills={bills}
              onSelectBill={setSelectedBillId}
            />

            <LineItemGrid
              bill={selectedBill}
              piiMaskingEnabled={piiMaskingEnabled}
              onOverrideCategory={(billId, itemId, newCat) => {
                overrideItemCategory(billId, itemId, newCat);
                addAuditLog({
                  type: 'state_mutation',
                  title: `Override Category: ${newCat}`,
                  tier: 2,
                  status: 'success',
                  toolName: 'override_line_item_category',
                  resultSummary: `User reclassified line item to '${newCat}'.`,
                  piiMaskedBeforeSend: piiMaskingEnabled,
                  latencyMs: 45,
                  fullPayload: { billId, itemId, newCat },
                });
              }}
              onSettleBill={handleSettleBillWithSecurity}
            />

            {/* Scheduled Recurring Bills & Income (GET /bills) */}
            <ScheduledBillsSection />
          </div>
        )}

        {/* TAB 3: SPENDING INSIGHTS & CASH FLOW CURVES */}
        {activeTab === 'insights' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <CashflowChart data={cashflowData} />
            <SpendingAnalytics
              categories={categories}
              transactions={transactions}
              onOpenCopilot={() => setActiveTab('copilot')}
              onOpenOptimizeModal={() => setIsSlidersModalOpen(true)}
            />
          </div>
        )}

        {/* TAB 4: CONVERSATIONAL AI ADVISORY COPILOT */}
        {activeTab === 'copilot' && (
          <div className="animate-in fade-in duration-200">
            <ChatDrawer
              messages={messages}
              isTyping={isTyping}
              inputValue={inputValue}
              setInputValue={setInputValue}
              onSendMessage={sendMessage}
              onExecuteRecommendation={executeRecommendation}
              currentTier={currentTier}
            />
          </div>
        )}

        {/* TAB 5: SECURITY & PERMISSION-TIER GATEWAY */}
        {activeTab === 'security' && (
          <div className="animate-in fade-in duration-200">
            <SecurityGatewayView
              currentTier={currentTier}
              setCurrentTier={setCurrentTier}
              tierConfigs={tierConfigs}
              piiMaskingEnabled={piiMaskingEnabled}
              onTogglePiiMasking={() => setPiiMaskingEnabled(!piiMaskingEnabled)}
              onOpenPiiModal={() => setIsPiiModalOpen(true)}
              onOpenAuditDrawer={() => setIsAuditDrawerOpen(true)}
              auditCount={auditLogs.length}
            />
          </div>
        )}
      </main>

      {/* Demo Seed Confirmation Modal (POST /demo/seed) */}
      <DemoSeedModal
        isOpen={isSeedModalOpen}
        onClose={() => setIsSeedModalOpen(false)}
        onSuccess={handleSeedSuccess}
      />

      {/* User Preferences & Financial Profile Modal (GET/PUT /profile) */}
      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        onProfileUpdated={(prof: UserProfile) => {
          addAuditLog({
            type: 'state_mutation',
            title: 'Updated Financial Preferences',
            tier: 2,
            status: 'success',
            resultSummary: `Profile currency ${prof.currency}, income $${minorToMajor(prof.monthly_income_minor).toFixed(2)}.`,
            piiMaskedBeforeSend: piiMaskingEnabled,
            latencyMs: 90,
            fullPayload: { ...prof },
          });
        }}
      />

      {/* New Transaction Manual Entry Modal (POST /transactions) */}
      <NewTransactionModal
        isOpen={isNewTxnModalOpen}
        onClose={() => setIsNewTxnModalOpen(false)}
        onTransactionCreated={handleTransactionCreated}
      />

      {/* Human-in-the-Loop PIN Modal (Tier 3 Authorization) */}
      <PinModal
        isOpen={isPinModalOpen}
        onClose={cancelPendingAction}
        pendingAction={pendingAction}
        onConfirmPin={confirmPinAndExecute}
      />

      {/* Sandbox Audit & Execution Evidence Drawer */}
      <AuditDrawer
        isOpen={isAuditDrawerOpen}
        onClose={() => setIsAuditDrawerOpen(false)}
        auditLogs={auditLogs}
        onExportLogs={exportAuditLogs}
      />

      {/* Client-Side PII Masking Preview Modal */}
      <PiiPreviewModal
        isOpen={isPiiModalOpen}
        onClose={() => setIsPiiModalOpen(false)}
        piiMaskingEnabled={piiMaskingEnabled}
        onTogglePiiMasking={() => setPiiMaskingEnabled(!piiMaskingEnabled)}
      />

      {/* Interactive Budget Reallocation Sliders Modal */}
      <BudgetSlidersModal
        isOpen={isSlidersModalOpen}
        onClose={() => setIsSlidersModalOpen(false)}
        categories={categories}
        onSaveAllocations={handleSaveAllocationsFromSliders}
        onApplyAiSuggestions={handleApplyAiOptimizationWithSecurity}
      />
    </div>
  );
}

export default App;
