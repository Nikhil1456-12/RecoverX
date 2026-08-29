import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { ClipboardList, ChevronLeft, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

const agentColors: Record<string, string> = {
  revenue_risk: 'bg-danger/10 text-danger',
  root_cause: 'bg-warning/10 text-warning',
  recovery_twin: 'bg-primary/10 text-primary',
  policy_engine: 'bg-primary/10 text-primary',
  recovery_policy: 'bg-accent/10 text-accent',
  action_executor: 'bg-accent/10 text-accent',
  evaluation: 'bg-primary/10 text-primary',
};

export default function AuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditLogs({ page: page.toString(), page_size: '30' })
      .then(data => { setLogs(data.logs); setTotal(data.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / 30);

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2"><ClipboardList className="w-6 h-6 text-primary" /> Audit Log</h1>
        <p className="text-text-secondary mt-1">{total.toLocaleString()} audit entries</p>
      </div>

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Time</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Transaction</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Agent</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Decision</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Action</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">State</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-8 text-text-secondary">Loading...</td></tr>
            ) : logs.map((log) => (
              <tr key={log.id} className="border-b border-border/50 hover:bg-surface-light/50">
                <td className="px-4 py-2.5 text-xs text-text-secondary">{new Date(log.created_at).toLocaleString()}</td>
                <td className="px-4 py-2.5 text-xs font-mono">{log.transaction_id}</td>
                <td className="px-4 py-2.5">
                  <span className={clsx('text-xs px-2 py-0.5 rounded', agentColors[log.agent] || 'bg-surface-lighter text-text-secondary')}>
                    {log.agent.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-xs">{log.decision_type}</td>
                <td className="px-4 py-2.5 text-xs">{log.action.replace(/_/g, ' ')}</td>
                <td className="px-4 py-2.5">
                  {log.previous_state && log.new_state ? (
                    <span className="text-xs">{log.previous_state} → <span className="font-medium">{log.new_state}</span></span>
                  ) : <span className="text-xs text-text-muted">—</span>}
                </td>
                <td className="px-4 py-2.5 text-xs">{log.confidence ? `${(log.confidence * 100).toFixed(0)}%` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-text-secondary">Page {page} of {totalPages}</p>
        <div className="flex items-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="p-2 rounded-lg hover:bg-surface-light disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
          <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page === totalPages} className="p-2 rounded-lg hover:bg-surface-light disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
        </div>
      </div>
    </div>
  );
}
