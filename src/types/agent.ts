export type SecurityTier = 1 | 2 | 3;

export interface SecurityTierInfo {
  tier: SecurityTier;
  name: string;
  badgeLabel: string;
  description: string;
  allowedActions: string[];
  restrictedActions: string[];
  requiresPin: boolean;
  colorScheme: 'slate' | 'amber' | 'emerald';
}

export type AuditEventType = 
  | 'tool_call'
  | 'state_mutation'
  | 'pii_sanitization'
  | 'pin_verification'
  | 'database_read';

export interface AuditLogEvent {
  id: string;
  timestamp: string;
  type: AuditEventType;
  title: string;
  tier: SecurityTier;
  status: 'success' | 'intercepted' | 'blocked' | 'simulated';
  toolName?: string;
  functionArgs?: Record<string, unknown>;
  resultSummary?: string;
  piiMaskedBeforeSend: boolean;
  pinVerified?: boolean;
  latencyMs: number;
  fullPayload: Record<string, unknown>;
}

export type ActionRecommendationType = 
  | 'budget_reallocate'
  | 'cancel_subscription'
  | 'fund_transfer'
  | 'bill_settle'
  | 'category_override';

export interface ActionRecommendation {
  id: string;
  type: ActionRecommendationType;
  title: string;
  description: string;
  impact: string;
  amount?: number;
  fromCategory?: string;
  toCategory?: string;
  targetMerchant?: string;
  tier: SecurityTier;
  executed: boolean;
  executionTimestamp?: string;
}

export interface CopilotMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  text: string;
  timestamp: string;
  recommendations?: ActionRecommendation[];
  thinking?: string;
  citations?: string[];
  toolResults?: Array<{ tool: string; result: Record<string, unknown> }>;
  tierRequired?: SecurityTier;
  isStreaming?: boolean;
}

export interface PendingSecurityAction {
  id: string;
  title: string;
  description: string;
  tierRequired: SecurityTier;
  mutationType: string;
  payload: Record<string, unknown>;
  onSuccess: () => void;
  onCancel?: () => void;
}
