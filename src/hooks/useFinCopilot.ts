import { useState, useCallback } from 'react';
import type { CopilotMessage, ActionRecommendation } from '../types/agent';
import type { MetricSummary } from '../types/financial';
import { endpoints } from '../api';

const INITIAL_MESSAGES: CopilotMessage[] = [
  {
    id: 'msg-welcome',
    sender: 'agent',
    text: `Hello! I am **Aura**, your autonomous financial copilot operating under **Tier 3 (State-Modifying Participant)**.

Ask me questions about your current cash flow, spending pace, bill audits, or budget recommendations.`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    citations: ['Active Ledger', 'POST /api/chat'],
  },
];

export function useFinCopilot(
  metrics: MetricSummary,
  onExecuteRecommendation: (rec: ActionRecommendation) => void
) {
  const [messages, setMessages] = useState<CopilotMessage[]>(INITIAL_MESSAGES);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [inputValue, setInputValue] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | null>(null);

  const executeRecommendation = useCallback((rec: ActionRecommendation) => {
    onExecuteRecommendation(rec);
    // Mark recommendation as executed in message list
    setMessages((prev) =>
      prev.map((msg) => ({
        ...msg,
        recommendations: msg.recommendations?.map((r) =>
          r.id === rec.id ? { ...r, executed: true, executionTimestamp: new Date().toLocaleTimeString() } : r
        ),
      }))
    );
  }, [onExecuteRecommendation]);

  const sendMessage = useCallback(
    async (userText: string) => {
      if (!userText.trim() || isTyping) return;

      const userMsg: CopilotMessage = {
        id: `msg-user-${Date.now()}`,
        sender: 'user',
        text: userText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInputValue('');
      setIsTyping(true);

      // Attempt remote POST /chat call first
      try {
        const response = await endpoints.chat.send({
          message: userText,
          conversation_id: conversationId,
        });

        const chatResult = response.result;
        setConversationId(chatResult.conversation_id);

        const agentMsg: CopilotMessage = {
          id: `msg-agent-${Date.now()}`,
          sender: 'agent',
          text: chatResult.message,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          toolResults: chatResult.tool_results as Array<{ tool: string; result: Record<string, unknown> }>,
          citations: chatResult.tool_results?.map((t) => `Tool: ${t.tool}`) || ['POST /chat API'],
        };

        setMessages((prev) => [...prev, agentMsg]);
        setIsTyping(false);
        return;
      } catch (err) {
        console.warn('API Chat endpoint returned error:', err);
        const errorText = err instanceof Error ? err.message : 'Unable to complete assistant generation.';
        const agentMsg: CopilotMessage = {
          id: `msg-agent-${Date.now()}`,
          sender: 'agent',
          text: `⚠️ **Assistant Request Notice**\n\n${errorText}\n\n*Live Ledger Metrics:*\n* **Total Inflow:** $${metrics.totalInflow.toFixed(2)}\n* **Discretionary Outflow:** $${metrics.discretionaryOutflow.toFixed(2)}\n* **Net Savings:** $${metrics.netSavings.toFixed(2)} (${metrics.savingsRate}%)\n* **Daily Burn:** $${metrics.dailyBurnRate.toFixed(2)}/day`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          citations: ['Live Ledger Metrics'],
        };
        setMessages((prev) => [...prev, agentMsg]);
        setIsTyping(false);
      }
    },
    [conversationId, isTyping, metrics]
  );

  return {
    messages,
    isTyping,
    inputValue,
    setInputValue,
    sendMessage,
    executeRecommendation,
    conversationId,
  };
}
