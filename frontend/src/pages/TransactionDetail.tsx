import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '@/services/api';
import { ArrowLeft, User, CreditCard, Clock, AlertCircle, CheckCircle, XCircle, Zap, Shield, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

const formatCurrency = (val: number) => `₹${val.toLocaleString('en-IN')}`;

const stateColors: Record<string, string> = {
  detected: 'text-warning',
  diagnosed: 'text-warning',
  simulating: 'text-primary',
  policy_check: 'text-primary',
  action_selected: 'text-primary',
  executing: 'text-primary',
  recovered: 'text-accent',
  failed: 'text-danger',
  stopped: 'text-text-muted',
};

export default function TransactionDetail() {
  const { id } = useParams<{ id: string }>();
  const [txn, setTxn] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [simulation, setSimulation] = useState<any>(null);
  const [recovering, setRecovering] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.getTransaction(id),
      api.getTimeline(id),
    ]).then(([txnData, timelineData]) => {
      setTxn(txnData);
      setTimeline(timelineData.timeline || []);
    }).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  const handleSimulate = async () => {
    if (!id) return;
    const result = await api.simulateRecovery(id);
    setSimulation(result);
  };

  const handleRecover = async () => {
    if (!id) return;
    setRecovering(true);
    try {
      const result = await api.recoverTransaction(id);
      // Refresh data
      const txnData = await api.getTransaction(id);
      setTxn(txnData);
      const timelineData = await api.getTimeline(id);
      setTimeline(timelineData.timeline || []);
      alert(result.message);
    } catch (err) { console.error(err); }
    finally { setRecovering(false); }
  };

  if (loading || !txn) return <div className="p-8 text-text-secondary">Loading...</div>;

  const customer = txn.customer;
  const twin = txn.recovery_twin;

  return (
    <div className="p-8">
      <Link to="/transactions" className="flex items-center gap-2 text-text-secondary hover:text-text-primary mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to Transactions
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold font-mono">{txn.id}</h1>
          <p className="text-text-secondary mt-1">{txn.failure_reason?.replace(/_/g, ' ') || 'Payment'} · {txn.payment_method.toUpperCase()}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold">{formatCurrency(txn.amount)}</p>
          <span className={clsx('inline-block px-3 py-1 rounded-lg text-sm font-medium mt-2', txn.status === 'recovered' ? 'bg-accent/10 text-accent' : txn.status === 'failed' ? 'bg-danger/10 text-danger' : 'bg-surface-lighter text-text-secondary')}>
            {txn.status.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Transaction Info */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><CreditCard className="w-4 h-4" /> Transaction Details</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div><p className="text-xs text-text-muted">Amount</p><p className="text-sm font-medium">{formatCurrency(txn.amount)}</p></div>
              <div><p className="text-xs text-text-muted">Payment Method</p><p className="text-sm font-medium uppercase">{txn.payment_method}</p></div>
              <div><p className="text-xs text-text-muted">Failure Reason</p><p className="text-sm font-medium">{txn.failure_reason?.replace(/_/g, ' ') || '—'}</p></div>
              <div><p className="text-xs text-text-muted">Type</p><p className="text-sm font-medium">{txn.transaction_type}</p></div>
              <div><p className="text-xs text-text-muted">Retry Count</p><p className="text-sm font-medium">{txn.retry_count}</p></div>
              <div><p className="text-xs text-text-muted">Created</p><p className="text-sm font-medium">{new Date(txn.created_at).toLocaleString()}</p></div>
            </div>
          </div>

          {/* Recovery Twin Scenarios */}
          {twin && twin.scenarios && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><Zap className="w-4 h-4" /> Recovery Twin Scenarios</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {twin.scenarios.map((s: any) => (
                  <div key={s.id} className={clsx('rounded-lg p-4 border transition-all', s.is_selected ? 'bg-primary/10 border-primary/30' : 'bg-surface-lighter/50 border-border/50 hover:border-border')}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{s.action.replace(/_/g, ' ')}</span>
                      {s.is_selected && <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">Selected</span>}
                    </div>
                    <p className="text-2xl font-bold">{(s.recovery_probability * 100).toFixed(0)}%</p>
                    <div className="mt-2 space-y-1 text-xs text-text-secondary">
                      <div className="flex justify-between"><span>Expected Revenue</span><span>{formatCurrency(s.expected_revenue)}</span></div>
                      <div className="flex justify-between"><span>Cost</span><span>₹{s.intervention_cost}</span></div>
                      <div className="flex justify-between"><span>Net Recovery</span><span className="font-medium text-text-primary">{formatCurrency(s.expected_net_recovery)}</span></div>
                    </div>
                  </div>
                ))}
              </div>
              {twin.explanation && (
                <div className="mt-4 bg-primary/5 border border-primary/20 rounded-lg p-4">
                  <p className="text-xs font-semibold text-primary mb-1">Why this action?</p>
                  <p className="text-sm text-text-primary">{twin.explanation}</p>
                </div>
              )}
            </div>
          )}

          {/* Timeline */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><Clock className="w-4 h-4" /> Recovery Timeline</h3>
            {timeline.length > 0 ? (
              <div className="space-y-4">
                {timeline.map((entry: any, i: number) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className={clsx('w-3 h-3 rounded-full', entry.new_state === 'recovered' ? 'bg-accent' : entry.new_state === 'failed' ? 'bg-danger' : 'bg-primary')} />
                      {i < timeline.length - 1 && <div className="w-px h-full bg-border min-h-[24px]" />}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-text-muted">{entry.time}</span>
                        <span className={clsx('text-sm font-medium', stateColors[entry.new_state] || 'text-text-primary')}>{entry.action.replace(/_/g, ' ')}</span>
                      </div>
                      {entry.reasoning && <p className="text-xs text-text-secondary mt-1">{entry.reasoning}</p>}
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-text-muted">No timeline data available</p>}
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Customer */}
          {customer && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><User className="w-4 h-4" /> Customer</h3>
              <div className="space-y-3">
                <div><p className="text-xs text-text-muted">Name</p><p className="text-sm font-medium">{customer.name}</p></div>
                <div><p className="text-xs text-text-muted">Segment</p><p className="text-sm font-medium capitalize">{customer.segment}</p></div>
                <div><p className="text-xs text-text-muted">Success Rate</p><p className="text-sm font-medium">{(customer.payment_success_rate * 100).toFixed(0)}%</p></div>
                <div><p className="text-xs text-text-muted">Lifetime Value</p><p className="text-sm font-medium">{formatCurrency(customer.lifetime_value)}</p></div>
                <div><p className="text-xs text-text-muted">DND</p><p className="text-sm font-medium">{customer.is_dnd ? 'Yes' : 'No'}</p></div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-text-secondary mb-4">Actions</h3>
            <div className="space-y-3">
              <button onClick={handleSimulate} className="w-full px-4 py-2.5 bg-primary/10 border border-primary/20 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors">
                Run Simulation
              </button>
              {txn.status === 'failed' && (
                <button onClick={handleRecover} disabled={recovering} className="w-full px-4 py-2.5 bg-accent/10 border border-accent/20 text-accent rounded-lg text-sm font-medium hover:bg-accent/20 transition-colors disabled:opacity-50">
                  {recovering ? 'Recovering...' : 'Execute Recovery'}
                </button>
              )}
              <Link to={`/what-if?txn=${txn.id}`} className="block w-full px-4 py-2.5 bg-surface-lighter border border-border text-text-primary rounded-lg text-sm font-medium text-center hover:bg-surface-light transition-colors">
                Open in What-If Lab
              </Link>
            </div>
          </div>

          {/* Simulation Results */}
          {simulation && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2"><Shield className="w-4 h-4" /> Live Simulation</h3>
              <div className="bg-accent/5 border border-accent/20 rounded-lg p-3 mb-3">
                <p className="text-xs text-text-muted">Recommended</p>
                <p className="text-sm font-bold text-accent">{simulation.recommended_action_label}</p>
              </div>
              <p className="text-xs text-text-secondary">{simulation.explanation}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
