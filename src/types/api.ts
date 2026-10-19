/**
 * Personal Finance Assistant API Implementation Contract Types
 * Corresponds to the Backend OpenAPI & API Reference Specification.
 */

// ==========================================
// Generic Envelope & Common Metadata Types
// ==========================================

export interface ApiEnvelope<T = unknown> {
  success: boolean;
  code: string;
  message: string;
  errors?: ApiValidationError[] | Record<string, unknown> | null;
  result: T;
  request_id: string;
}

export interface ApiValidationError {
  field?: string;
  message: string;
}

export interface CommonEntityMetadata {
  entity_type: string;
  created_at: string;
  updated_at: string;
  version: number;
}

// ==========================================
// Auth & Identity
// ==========================================

export interface AuthMeResult {
  user_id: string;
  email: string | null;
  username: string | null;
  scopes: string[];
  groups: string[];
}

// ==========================================
// Profile & Preferences
// ==========================================

export interface UserProfile extends Partial<CommonEntityMetadata> {
  currency: string;
  timezone: string;
  monthly_income_minor: number;
  opening_balance_minor: number;
  safety_buffer_minor: number;
}

export interface ProfileUpdatePayload {
  currency?: string;
  timezone?: string;
  monthly_income_minor: number;
  opening_balance_minor: number;
  safety_buffer_minor: number;
}

export interface DemoSeedResult {
  seeded: boolean;
  item_count: number;
}

// ==========================================
// Accounts
// ==========================================

export type AccountType = 'checking' | 'savings' | 'credit' | 'investment' | string;

export interface AccountItem extends CommonEntityMetadata {
  entity_type: 'ACCOUNT';
  account_id: string;
  name: string;
  account_type: AccountType;
  balance_minor: number;
  currency: string;
}

// ==========================================
// Transactions
// ==========================================

export type ApiTransactionType = 'income' | 'expense' | 'transfer' | 'refund';
export type ApiTransactionSource = 'manual' | 'seed' | 'receipt' | 'agent';

export interface ApiTransactionItem extends CommonEntityMetadata {
  entity_type: 'TXN';
  transaction_id: string;
  account_id: string;
  amount_minor: number;
  currency: string;
  transaction_type: ApiTransactionType;
  category: string;
  merchant: string;
  posted_at: string; // YYYY-MM-DD
  source: ApiTransactionSource;
  notes: string | null;
  receipt_id: string | null;
}

export interface TransactionFilterParams {
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  category?: string;
  transaction_type?: ApiTransactionType;
  limit?: number; // 1..200
  cursor?: string;
}

export interface TransactionListResult {
  items: ApiTransactionItem[];
  next_cursor: string | null;
}

export interface CreateTransactionPayload {
  account_id?: string;
  amount_minor: number;
  currency?: string;
  transaction_type: ApiTransactionType;
  category: string;
  merchant: string;
  posted_at: string; // YYYY-MM-DD
  source?: ApiTransactionSource;
  notes?: string;
}

export interface PatchTransactionPayload {
  category?: string;
  merchant?: string;
  notes?: string;
}

// ==========================================
// Budgets
// ==========================================

export interface ApiBudgetItem extends CommonEntityMetadata {
  entity_type: 'BUDGET';
  month: string; // YYYY-MM
  category: string;
  limit_minor: number;
  currency: string;
  spent_minor: number;
  remaining_minor: number;
  utilization: number; // e.g. 0.3533 (can exceed 1.0)
}

export interface BudgetListResult {
  month: string;
  items: ApiBudgetItem[];
}

export interface UpdateBudgetPayload {
  limit_minor: number;
  currency?: string;
}

// ==========================================
// Bills & Scheduled Income
// ==========================================

export type BillKind = 'expense' | 'income';
export type BillFrequency = 'once' | 'weekly' | 'monthly';

export interface ApiBillItem extends CommonEntityMetadata {
  entity_type: 'BILL';
  bill_id: string;
  name: string;
  amount_minor: number;
  currency: string;
  category: string;
  kind: BillKind;
  next_due_date: string; // YYYY-MM-DD
  frequency: BillFrequency;
  active: boolean;
}

export interface CreateBillPayload {
  name: string;
  amount_minor: number;
  currency?: string;
  category: string;
  kind: BillKind;
  next_due_date: string; // YYYY-MM-DD
  frequency: BillFrequency;
  active?: boolean;
}

export interface PatchBillPayload {
  name?: string;
  amount_minor?: number;
  category?: string;
  next_due_date?: string;
  frequency?: BillFrequency;
  active?: boolean;
}

// ==========================================
// Dashboard & Forecast
// ==========================================

export interface DashboardBalance {
  balance_minor: number;
  currency: string;
  accounts: AccountItem[];
}

export interface DashboardSummary {
  month: string;
  income_minor: number;
  spending_minor: number;
  net_minor: number;
  category_totals: Record<string, number>;
  top_merchants: [string, number][]; // [merchantName, amountMinor]
}

export type InsightType =
  | 'budget_exceeded'
  | 'budget_warning'
  | 'negative_balance'
  | 'safety_buffer'
  | string;

export interface DashboardInsight {
  type: InsightType;
  category?: string;
  amount_minor?: number;
  utilization?: number;
  date?: string;
  balance_minor?: number;
  message?: string;
}

export interface DashboardResult {
  balance: DashboardBalance;
  summary: DashboardSummary;
  budgets: ApiBudgetItem[];
  upcoming_bills: ApiBillItem[];
  forecast: ForecastResult;
  insights: DashboardInsight[];
}

export interface ForecastPoint {
  date: string; // YYYY-MM-DD
  projected_minor: number;
  lower_minor: number;
  upper_minor: number;
  scheduled_income_minor: number;
  scheduled_expense_minor: number;
}

export interface ForecastResult {
  days: number;
  starting_balance_minor: number;
  daily_discretionary_mean_minor: number;
  daily_discretionary_std_minor: number;
  confidence: number; // 0.0 - 1.0
  points: ForecastPoint[];
  alerts: Array<{
    type: string;
    message: string;
    date?: string;
    severity?: string;
  }>;
}

// ==========================================
// Receipts
// ==========================================

export type ReceiptStatus = 'parsed' | 'needs_review';

export interface ReceiptExtraction {
  merchant: string;
  transaction_date: string; // YYYY-MM-DD
  subtotal_minor: number;
  tax_minor: number;
  total_minor: number;
  currency: string;
  category: string;
  line_items: Array<{
    description?: string;
    quantity?: number;
    amount_minor?: number;
  }>;
  confidence: number; // 0.0 - 1.0
}

export interface ApiReceiptItem extends CommonEntityMetadata {
  entity_type: 'RECEIPT';
  receipt_id: string;
  content_type: string;
  status: ReceiptStatus;
  extraction: ReceiptExtraction;
  transaction_id: string | null;
}

export interface PatchReceiptPayload {
  merchant?: string;
  transaction_date?: string;
  total_minor?: number;
  currency?: string;
  category?: string;
  confirm?: boolean;
}

// ==========================================
// Assistant / Chat & Conversations
// ==========================================

export interface ChatMessagePayload {
  message: string;
  conversation_id?: string | null;
}

export interface ChatToolResult {
  tool: string;
  result: Record<string, unknown>;
}

export interface ChatMessageResult {
  conversation_id: string;
  message: string;
  tool_results: ChatToolResult[];
}

export interface ConversationItem extends CommonEntityMetadata {
  entity_type: 'CONV';
  conversation_id: string;
  title: string;
}

export interface ConversationMessageItem extends CommonEntityMetadata {
  entity_type: 'MSG';
  conversation_id: string;
  message_id: string;
  role: 'user' | 'assistant' | 'system' | string;
  content: string;
  tool_data?: Record<string, unknown>;
}

export interface ConversationDetailResult {
  conversation: ConversationItem;
  messages: ConversationMessageItem[];
}

// ==========================================
// Known Error Codes
// ==========================================

export const API_ERROR_CODES = {
  // Auth
  AUTH_TOKEN_MISSING: 'AUTH_TOKEN_MISSING',
  AUTH_TOKEN_EXPIRED: 'AUTH_TOKEN_EXPIRED',
  AUTH_TOKEN_INVALID: 'AUTH_TOKEN_INVALID',
  AUTH_ISSUER_INVALID: 'AUTH_ISSUER_INVALID',
  AUTH_CLIENT_INVALID: 'AUTH_CLIENT_INVALID',
  AUTH_TOKEN_TYPE_INVALID: 'AUTH_TOKEN_TYPE_INVALID',
  AUTH_JWKS_UNAVAILABLE: 'AUTH_JWKS_UNAVAILABLE',

  // Profile
  FIN_PROFILE_NOT_FOUND: 'FIN_PROFILE_NOT_FOUND',
  FIN_PROFILE_UPDATED: 'FIN_PROFILE_UPDATED',

  // Transactions
  FIN_TRANSACTION_CREATED: 'FIN_TRANSACTION_CREATED',
  FIN_TRANSACTION_NOT_FOUND: 'FIN_TRANSACTION_NOT_FOUND',

  // Budgets
  FIN_BUDGET_UPDATED: 'FIN_BUDGET_UPDATED',

  // Bills
  FIN_BILL_CREATED: 'FIN_BILL_CREATED',
  FIN_BILL_NOT_FOUND: 'FIN_BILL_NOT_FOUND',

  // Receipts
  FIN_RECEIPT_NOT_FOUND: 'FIN_RECEIPT_NOT_FOUND',
  FIN_RECEIPT_DUPLICATE: 'FIN_RECEIPT_DUPLICATE',
  FIN_RECEIPT_TOO_LARGE: 'FIN_RECEIPT_TOO_LARGE',
  FIN_RECEIPT_INVALID: 'FIN_RECEIPT_INVALID',

  // General & AI
  FIN_FORECAST_INVALID: 'FIN_FORECAST_INVALID',
  FIN_TOOL_INVALID: 'FIN_TOOL_INVALID',
  FIN_UNSAFE_ACTION: 'FIN_UNSAFE_ACTION',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  AWS_DYNAMODB_ERROR: 'AWS_DYNAMODB_ERROR',
  AWS_S3_ERROR: 'AWS_S3_ERROR',
  AI_GEMINI_UNAVAILABLE: 'AI_GEMINI_UNAVAILABLE',
} as const;

export type ApiErrorCode = (typeof API_ERROR_CODES)[keyof typeof API_ERROR_CODES];
