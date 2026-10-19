export type TransactionType = 'income' | 'expense';
export type TransactionStatus = 'settled' | 'pending';

export interface PiiData {
  cardPan?: string;
  iban?: string;
  address?: string;
  ssnTaxId?: string;
}

export interface Transaction {
  id: string;
  date: string;
  merchant: string;
  category: string;
  amount: number;
  type: TransactionType;
  status: TransactionStatus;
  piiRaw?: PiiData;
  piiMasked?: PiiData;
  isAnomaly?: boolean;
  notes?: string;
  paymentMethod: string;
}

export interface CategoryBudget {
  id: string;
  name: string;
  icon: string;
  allocated: number;
  spent: number;
  aiSuggested: number;
  velocity: number; // spend rate % against ideal daily spend
  period: 'monthly';
  color: string;
  isAlert?: boolean;
}

export interface CashflowPoint {
  date: string;
  dayLabel: string;
  income: number;
  expense: number;
  netBalance: number;
  projectedBalance?: number;
  burnRateUpper?: number;
  burnRateLower?: number;
  isProjected?: boolean;
}

export interface BillLineItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  amount: number;
  category: string;
  confidence: number; // 0 to 1
  isAnomaly?: boolean;
}

export interface ExtractedBill {
  id: string;
  fileName: string;
  fileType: 'pdf' | 'png' | 'jpeg' | 'webp';
  fileSize: string;
  uploadTime: string;
  merchant: string;
  invoiceDate: string;
  invoiceNumber: string;
  subtotal: number;
  taxRate: number;
  taxAmount: number;
  totalAmount: number;
  status: 'processing' | 'extracted' | 'verified';
  confidenceScore: number;
  items: BillLineItem[];
  piiDetected: boolean;
  rawPii: PiiData;
  maskedPii: PiiData;
  previewUrl?: string;
}

export interface DeficitWarning {
  id: string;
  severity: 'warning' | 'danger' | 'info';
  title: string;
  message: string;
  category: string;
  projectedDeficitDate: string;
  recommendedAction: string;
  potentialImpact: number;
}

export interface MetricSummary {
  totalInflow: number;
  discretionaryOutflow: number;
  fixedOutflow: number;
  netSavings: number;
  savingsRate: number; // percentage
  dailyBurnRate: number;
  runwayDays: number;
  healthScore: number; // 0 - 100
  scoreChange: number;
  safeToSpendDaily: number;
}
