import React, { useState } from 'react';
import {
  X,
  Download,
  Terminal,
  Search,
  Copy,
  Check,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  Database,
  Eye,
  KeyRound,
  Wrench,
} from 'lucide-react';

import type { AuditLogEvent, AuditEventType } from '../../types/agent';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface AuditDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  auditLogs: AuditLogEvent[];
  onExportLogs: () => void;
}

export const AuditDrawer: React.FC<AuditDrawerProps> = ({
  isOpen,
  onClose,
  auditLogs,
  onExportLogs,
}) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedLogId, setExpandedLogId] = useState<string | null>(auditLogs[0]?.id || null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!isOpen) return null;

  const filteredLogs = auditLogs.filter((log) => {
    const matchesFilter = filterType === 'all' || log.type === filterType;
    const matchesSearch =
      searchQuery === '' ||
      log.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.toolName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resultSummary?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleCopyJson = (log: AuditLogEvent) => {
    navigator.clipboard.writeText(JSON.stringify(log, null, 2));
    setCopiedId(log.id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const getEventIcon = (type: AuditEventType) => {
    switch (type) {
      case 'tool_call':
        return <Wrench className="w-4 h-4 text-sky-400" />;
      case 'state_mutation':
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
      case 'pii_sanitization':
        return <Eye className="w-4 h-4 text-purple-400" />;
      case 'pin_verification':
        return <KeyRound className="w-4 h-4 text-amber-400" />;
      case 'database_read':
        return <Database className="w-4 h-4 text-blue-400" />;
      default:
        return <Terminal className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status: AuditLogEvent['status']) => {
    switch (status) {
      case 'success':
        return <Badge variant="emerald" size="sm">Committed</Badge>;
      case 'intercepted':
        return <Badge variant="amber" size="sm">HITL Intercepted</Badge>;
      case 'blocked':
        return <Badge variant="rose" size="sm">Blocked</Badge>;
      case 'simulated':
        return <Badge variant="sky" size="sm">Simulated</Badge>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Slide-over Drawer Panel */}
      <div className="relative w-full max-w-2xl bg-slate-950 border-l border-slate-800 shadow-2xl h-full flex flex-col z-10 animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight m-0">
                  Execution Evidence Inspector
                </h2>
                <span className="text-[10px] font-mono font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2 py-0.5 rounded-full">
                  Sandbox Log
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Audit trail for Topic A: AI as a Financial Participant submission criteria
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onExportLogs}
              leftIcon={<Download className="w-3.5 h-3.5 text-sky-400" />}
            >
              Export JSON
            </Button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/40 space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search tool names, arguments, or result summaries..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>

          {/* Event Type Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {[
              { id: 'all', label: 'All Records' },
              { id: 'tool_call', label: 'Tool Calls' },
              { id: 'state_mutation', label: 'State Mutations' },
              { id: 'pii_sanitization', label: 'PII Scrubbing' },
              { id: 'pin_verification', label: 'PIN HITL' },
              { id: 'database_read', label: 'DB Reads' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilterType(tab.id)}
                className={`px-2.5 py-1 rounded-lg font-medium whitespace-nowrap transition-colors ${
                  filterType === tab.id
                    ? 'bg-sky-500 text-slate-950 font-bold'
                    : 'bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Logs List Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No audit logs match current filter criteria.
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isExpanded = expandedLogId === log.id;
              return (
                <div
                  key={log.id}
                  className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden transition-all duration-200 hover:border-slate-700"
                >
                  {/* Event summary row */}
                  <div
                    onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                    className="p-3.5 flex items-start justify-between gap-3 cursor-pointer select-none"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 shrink-0 mt-0.5">
                        {getEventIcon(log.type)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{log.title}</span>
                          <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                            Tier {log.tier}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                          {log.resultSummary}
                        </p>
                        <div className="flex items-center gap-3 text-[10px] text-slate-500 font-mono mt-1.5">
                          <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                          <span>•</span>
                          <span>Latency: {log.latencyMs}ms</span>
                          {log.toolName && (
                            <>
                              <span>•</span>
                              <span className="text-sky-400">tool: {log.toolName}()</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {getStatusBadge(log.status)}
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Raw JSON Expanded View */}
                  {isExpanded && (
                    <div className="border-t border-slate-800/80 bg-slate-950 p-3.5 space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="font-mono">JSON Function Payload & State Signature:</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyJson(log);
                          }}
                          className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-medium"
                        >
                          {copiedId === log.id ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              <span>Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy JSON</span>
                            </>
                          )}
                        </button>
                      </div>

                      <pre className="p-3 rounded-xl bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto leading-relaxed max-h-56">
                        {JSON.stringify(log.fullPayload, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between text-xs text-slate-400">
          <span>{filteredLogs.length} audit trail records displayed</span>
          <span className="text-[11px] text-slate-400">
            Immutable SHA-256 verifiable sandbox session
          </span>
        </div>
      </div>
    </div>
  );
};
