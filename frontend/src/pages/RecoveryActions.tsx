import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Zap, CheckCircle, XCircle } from 'lucide-react';
import { clsx } from 'clsx';

const formatCurrency = (val: number) => `₹${val.toLocaleString('en-IN')}`;

export default function RecoveryActions() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecoveryActions().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-text-secondary">Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold flex items-center gap-2 mb-6"><Zap className="w-6 h-6 text-primary" /> Recovery Actions</h1>

      {data?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="stat-card"><p className="kpi-label">Total Actions</p><p className="kpi-value">{data.summary.total_actions}</p></div>
          <div className="stat-card"><p className="kpi-label">Successful</p><p className="kpi-value text-accent">{data.summary.successful}</p></div>
          <div className="stat-card"><p className="kpi-label">Success Rate</p><p className="kpi-value">{(data.summary.success_rate * 100).toFixed(1)}%</p></div>
          <div className="stat-card"><p className="kpi-label">Total Recovered</p><p className="kpi-value text-accent">{formatCurrency(data.summary.total_recovered)}</p></div>
        </div>
      )}

      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Action ID</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Transaction</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Type</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Result</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase">Cost</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase">Recovered</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase">Executed</th>
            </tr>
          </thead>
          <tbody>
            {data?.actions?.slice(0, 50).map((a: any) => (
              <tr key={a.id} className="border-b border-border/50 hover:bg-surface-light/50">
                <td className="px-4 py-3 text-sm font-mono">{a.id}</td>
                <td className="px-4 py-3 text-sm font-mono">{a.transaction_id}</td>
                <td className="px-4 py-3 text-sm">{a.action_type.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3">
                  <span className={clsx('flex items-center gap-1 text-sm', a.result === 'success' ? 'text-accent' : 'text-danger')}>
                    {a.result === 'success' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                    {a.result}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right">₹{a.cost}</td>
                <td className="px-4 py-3 text-sm text-right font-medium">{a.outcome ? formatCurrency(a.outcome.recovered_amount) : '—'}</td>
                <td className="px-4 py-3 text-sm text-text-secondary">{a.executed_at ? new Date(a.executed_at).toLocaleDateString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
