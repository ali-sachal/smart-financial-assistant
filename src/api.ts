import { fetchAuthSession } from 'aws-amplify/auth';
import type {
  ApiEnvelope,
  AuthMeResult,
  UserProfile,
  ProfileUpdatePayload,
  DemoSeedResult,
  AccountItem,
  ApiTransactionItem,
  TransactionFilterParams,
  TransactionListResult,
  CreateTransactionPayload,
  PatchTransactionPayload,
  BudgetListResult,
  ApiBudgetItem,
  UpdateBudgetPayload,
  ApiBillItem,
  CreateBillPayload,
  PatchBillPayload,
  DashboardResult,
  ForecastResult,
  ApiReceiptItem,
  PatchReceiptPayload,
  ChatMessagePayload,
  ChatMessageResult,
  ConversationDetailResult,
} from './types/api';

export * from './types/api';

/**
 * Custom Error Class that retains response envelope details (request_id, error code, structured errors)
 */
export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly requestId?: string;
  public readonly errors?: unknown;
  public readonly responseTime?: string | null;

  constructor(params: {
    status: number;
    code: string;
    message: string;
    requestId?: string;
    errors?: unknown;
    responseTime?: string | null;
  }) {
    super(params.message);
    this.name = 'ApiError';
    this.status = params.status;
    this.code = params.code;
    this.requestId = params.requestId;
    this.errors = params.errors;
    this.responseTime = params.responseTime;
  }

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isDuplicateReceipt(): boolean {
    return this.status === 409;
  }

  get isUnsafeAction(): boolean {
    return this.status === 403;
  }

  get isValidationError(): boolean {
    return this.status === 422;
  }
}

// ==========================================
// Money & Format Utilities
// ==========================================

/**
 * Converts minor currency units (e.g. 12345 cents) to major units (123.45 dollars).
 */
export function minorToMajor(minor: number): number {
  return (minor || 0) / 100;
}

/**
 * Converts major currency units (e.g. 123.45 dollars) to integer minor units (12345 cents).
 * Never send floating-point numbers to the backend.
 */
export function majorToMinor(major: number): number {
  return Math.round((major || 0) * 100);
}

/**
 * Formats integer minor units for localized display (e.g. 12345 -> "$123.45").
 */
export function formatCurrencyMinor(
  minor: number,
  currency = 'USD',
  locale = 'en-US'
): string {
  const major = minorToMajor(minor);
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(major);
  } catch {
    return `$${major.toFixed(2)}`;
  }
}

/**
 * Formats a budget utilization decimal ratio to a display percentage (e.g. 0.3533 -> "35.3%").
 * Utilization can exceed 100%.
 */
export function formatUtilization(ratio: number): string {
  const pct = (ratio || 0) * 100;
  return `${pct.toFixed(1)}%`;
}

/**
 * Formats confidence decimal ratio (0.0 to 1.0) to percentage (e.g. 0.95 -> "95%").
 */
export function formatConfidence(ratio: number): string {
  const pct = Math.max(0, Math.min(1, ratio || 0)) * 100;
  return `${pct.toFixed(0)}%`;
}

// ==========================================
// Request UUID & Base Config
// ==========================================

function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'req-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now().toString(36);
}

export function buildFullUrl(path: string): string {
  const envBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  let base = envBase ? envBase.replace(/\/+$/, '') : 'http://127.0.0.1:8000/api';

  // Ensure base ends with /api
  if (!base.endsWith('/api')) {
    base = `${base}/api`;
  }

  // Strip redundant leading /api from path to prevent /api/api/...
  const cleanPath = path.replace(/^\/?api(\/|$)/, '/');
  const normalizedPath = cleanPath.startsWith('/') ? cleanPath : `/${cleanPath}`;

  return `${base}${normalizedPath}`;
}

export interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
  requestId?: string;
}

/**
 * Low-level typed fetch wrapper adhering to the implementation contract:
 * - Sends Authorization: Bearer <cognito-access-token> (Cognito sub is verified by backend, no user_id sent)
 * - Sends and captures X-Request-ID
 * - Reads X-Response-Time
 * - Parses standard ApiResponse envelope
 */
export async function rawApiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<ApiEnvelope<T>> {
  const { requiresAuth = true, requestId = generateRequestId(), ...fetchOptions } = options;

  const headers = new Headers(fetchOptions.headers);
  headers.set('X-Request-ID', requestId);

  if (requiresAuth) {
    try {
      const session = await fetchAuthSession();
      // Implementation contract strictly requires an access token (never an ID token)
      const accessToken = session.tokens?.accessToken?.toString();

      if (!accessToken) {
        throw new ApiError({
          status: 401,
          code: 'AUTH_TOKEN_MISSING',
          message: 'Cognito access token is missing. Please sign in.',
          requestId,
        });
      }

      headers.set('Authorization', `Bearer ${accessToken}`);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError({
        status: 401,
        code: 'AUTH_TOKEN_MISSING',
        message: err instanceof Error ? err.message : 'Please sign in first.',
        requestId,
      });
    }
  }

  // Set Content-Type only if body is not FormData and not already set
  if (
    fetchOptions.body &&
    !(fetchOptions.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json');
  }

  const fullUrl = buildFullUrl(path);

  let response: Response;
  try {
    response = await fetch(fullUrl, {
      ...fetchOptions,
      headers,
    });
  } catch (netErr) {
    throw new ApiError({
      status: 0,
      code: 'NETWORK_ERROR',
      message:
        netErr instanceof Error
          ? `Network connection error: ${netErr.message}`
          : 'Failed to connect to backend server.',
      requestId,
    });
  }

  const responseTime = response.headers.get('X-Response-Time');
  const serverRequestId = response.headers.get('X-Request-ID') || requestId;

  let json: ApiEnvelope<T>;
  try {
    json = (await response.json()) as ApiEnvelope<T>;
  } catch {
    const rawText = await response.text().catch(() => '');
    throw new ApiError({
      status: response.status,
      code: response.ok ? 'INVALID_RESPONSE' : 'SERVER_ERROR',
      message: rawText || `HTTP ${response.status} ${response.statusText}`,
      requestId: serverRequestId,
      responseTime,
    });
  }

  if (!response.ok || !json.success) {
    throw new ApiError({
      status: response.status,
      code: json.code || `HTTP_${response.status}`,
      message: json.message || response.statusText || 'An unexpected error occurred.',
      requestId: json.request_id || serverRequestId,
      errors: json.errors,
      responseTime,
    });
  }

  return json;
}

/**
 * Standard convenience wrapper returning the unwrapped `result` or full envelope
 */
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const envelope = await rawApiRequest<T>(path, options);
  return envelope.result;
}

// ==========================================
// Endpoints API Client Object
// ==========================================

export const endpoints = {
  // Liveness check (public, no auth)
  health: {
    check: () =>
      rawApiRequest<{ status: string }>('/health/check', {
        method: 'GET',
        requiresAuth: false,
      }),
  },

  // Auth / Identity
  auth: {
    me: () =>
      rawApiRequest<AuthMeResult>('/auth/me', {
        method: 'GET',
      }),
  },

  // Profile preferences
  profile: {
    get: () =>
      rawApiRequest<UserProfile>('/profile', {
        method: 'GET',
      }),
    update: (payload: ProfileUpdatePayload) =>
      rawApiRequest<UserProfile>('/profile', {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
  },

  // Demo seed (Destructive: resets user's partition with deterministic demo items)
  demo: {
    seed: () =>
      rawApiRequest<DemoSeedResult>('/demo/seed', {
        method: 'POST',
      }),
  },

  // Accounts
  accounts: {
    list: () =>
      rawApiRequest<AccountItem[]>('/accounts', {
        method: 'GET',
      }),
  },

  // Transactions
  transactions: {
    list: (params?: TransactionFilterParams) => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.set('start_date', params.start_date);
      if (params?.end_date) searchParams.set('end_date', params.end_date);
      if (params?.category) searchParams.set('category', params.category);
      if (params?.transaction_type) searchParams.set('transaction_type', params.transaction_type);
      if (params?.limit) searchParams.set('limit', params.limit.toString());
      if (params?.cursor) searchParams.set('cursor', params.cursor);

      const qs = searchParams.toString();
      return rawApiRequest<TransactionListResult>(`/transactions${qs ? `?${qs}` : ''}`, {
        method: 'GET',
      });
    },

    create: (payload: CreateTransactionPayload) =>
      rawApiRequest<ApiTransactionItem>('/transactions', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    patch: (transactionId: string, payload: PatchTransactionPayload) =>
      rawApiRequest<ApiTransactionItem>(`/transactions/${encodeURIComponent(transactionId)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
  },

  // Budgets
  budgets: {
    get: (month: string, category: string) =>
      rawApiRequest<BudgetListResult>(
        `/budgets/${encodeURIComponent(month)}/${encodeURIComponent(category.toLowerCase())}`,
        {
          method: 'GET',
        }
      ),

    update: (month: string, category: string, payload: UpdateBudgetPayload) =>
      rawApiRequest<ApiBudgetItem>(
        `/budgets/${encodeURIComponent(month)}/${encodeURIComponent(category.toLowerCase())}`,
        {
          method: 'PUT',
          body: JSON.stringify(payload),
        }
      ),
  },

  // Bills and scheduled income
  bills: {
    list: (days = 30) =>
      rawApiRequest<ApiBillItem[]>(`/bills?days=${Math.max(1, Math.min(365, days))}`, {
        method: 'GET',
      }),

    create: (payload: CreateBillPayload) =>
      rawApiRequest<ApiBillItem>('/bills', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    patch: (billId: string, payload: PatchBillPayload) =>
      rawApiRequest<ApiBillItem>(`/bills/${encodeURIComponent(billId)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
  },

  // Dashboard aggregated data
  dashboard: {
    get: (month?: string) => {
      const qs = month ? `?month=${encodeURIComponent(month)}` : '';
      return rawApiRequest<DashboardResult>(`/dashboard${qs}`, {
        method: 'GET',
      });
    },
  },

  // Forecast cash-flow
  forecast: {
    get: (days = 30) => {
      const boundedDays = Math.max(1, Math.min(90, days));
      return rawApiRequest<ForecastResult>(`/forecast?days=${boundedDays}`, {
        method: 'GET',
      });
    },
  },

  // Receipts OCR and extraction
  receipts: {
    scan: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      return rawApiRequest<ApiReceiptItem>('/receipts/scan', {
        method: 'POST',
        body: formData,
      });
    },

    get: (receiptId: string) =>
      rawApiRequest<ApiReceiptItem>(`/receipts/${encodeURIComponent(receiptId)}`, {
        method: 'GET',
      }),

    patch: (receiptId: string, payload: PatchReceiptPayload) =>
      rawApiRequest<ApiReceiptItem>(`/receipts/${encodeURIComponent(receiptId)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
  },

  // Copilot Assistant & Chat
  chat: {
    send: (payload: ChatMessagePayload) =>
      rawApiRequest<ChatMessageResult>('/chat', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  // Conversations history
  conversations: {
    get: (conversationId: string) =>
      rawApiRequest<ConversationDetailResult>(
        `/conversations/${encodeURIComponent(conversationId)}`,
        {
          method: 'GET',
        }
      ),
  },
};

export default endpoints;
