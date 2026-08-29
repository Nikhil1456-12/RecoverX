import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { useSearchParams } from 'react-router-dom';
import { FlaskConical, Search, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

const formatCurrency = (val: number) => `₹${val.toLocaleString('en-IN')}`;

const actionLabels: Record<string, string> = {
  retry_now: 'Retry Now',
  retry_15m: 'Retry in 15 min',
  retry_45m: 'Retry in 45 min',
  whatsapp: 'WhatsApp',
  payment_link: 'Payment Link',
  sms: 'SMS',
  email: 'Email',
  human_escalation: 'Human Escalation',
  stop: 'Stop Recovery',
};

export default function WhatIfLab() {
  const [searchParams] = useSearchParams();
  const [txnId, setTxnId] = useState(searchParams.get('txn') || '');
  const [txn, setTxn] = useState<any>(null);
  const [simulation, setSimulation] = useState<any>(null);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!txnId) return;
    setLoading(true);
    try {
      const [txnData, simData] = await Promise.all([
        api.getTransaction(txnId),
        api.simulateRecovery(txnId),
      ]);
      setTxn(txnData);
      setSimulation(simData);
      setSelectedAction(simData.recommended_action);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (txnId) handleSearch();
  }, []);

  const selectedScenario = simulation?.scenarios?.find((s: any) => s.action === selectedAction);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-2"><FlaskConical className="w-6 h-6 text-primary" /> Recovery What-If Lab</h1>
        <p className="text-text-secondary mt-1">Simulate and compare recovery interventions for any transaction</p>
      </div>

      {/* Search */}
      <div className="glass-card p-4 mb-8">
        <div className="flex gap-3">
          <input
            type="text"
            value={txnId}
            onChange={e => setTxnId(e.target.value)}
            placeholder="Enter Transaction ID (e.g., TXN_000001)"
            className="flex-1 bg-surface-lighter border border-border rounded-lg px-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-primary font-mono"
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} disabled={loading} className="px-6 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors disabled:opacity-50 flex items-center gap-2">
            <Search className="w-4 h-4" /> {loading ? 'Loading...' : 'Analyze'}
          </button>
        </div>
      </div>

      {txn && simulation && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Transaction Info */}
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-text-secondary mb-4">Transaction</h3>
              <div className="space-y-3">
                <div><p className="text-xs text-text-muted">ID</p><p className="text-sm font-mono">{txn.id}</p></div>
                <div><p className="text-xs text-text-muted">Amount</p><p className="text-xl font-bold">{formatCurrency(txn.amount)}</p></div>
                <div><p className="text-xs text-text-muted">Payment Method</p><p className="text-sm uppercase">{txn.payment_method}</p></div>
                <div><p className="text-xs text-text-muted">Failure Reason</p><p className="text-sm">{txn.failure_reason?.replace(/_/g, ' ')}</p></div>
                <div><p className="text-xs text-text-muted">Status</p><p className="text-sm font-medium">{txn.status}</p></div>
              </div>
              {txn.customer && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-xs text-text-muted mb-2">Customer</p>
                  <p className="text-sm">{txn.customer.name}</p>
                  <p className="text-xs text-text-secondary">Success rate: {(txn.customer.payment_success_rate * 100).toFixed(0)}%</p>
                  <p className="text-xs text-text-secondary">Segment: {txn.customer.segment}</p>
                </div>
              )}
            </div>
          </div>

          {/* Right: Scenario Cards */}
          <div className="lg:col-span-2">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {simulation.scenarios.filter((s: any) => s.action !== 'stop').map((s: any) => (
                <button
                  key={s.action}
                  onClick={() => setSelectedAction(s.action)}
                  className={clsx(
                    'text-left rounded-xl p-5 border transition-all',
                    s.action === selectedAction
                      ? 'bg-primary/10 border-primary/40 ring-1 ring-primary/20'
                      : s.is_recommended
                      ? 'bg-accent/5 border-accent/20 hover:border-accent/40'
                      : 'bg-surface-light border-border hover:border-border/80'
                  )}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium">{actionLabels[s.action] || s.action}</span>
                    {s.is_recommended && <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">Best</span>}
                  </div>
                  <p className="text-3xl font-bold mb-1">{(s.recovery_probability * 100).toFixed(0)}%</p>
                  <div className="space-y-1 text-xs text-text-secondary">
                    <div className="flex justify-between"><span>Expected Revenue</span><span className="text-text-primary">{formatCurrency(s.expected_revenue)}</span></div>
                    <div className="flex justify-between"><span>Cost</span><span>₹{s.intervention_cost}</span></div>
                    <div className="flex justify-between"><span>Friction</span><span>{(s.friction_score * 100).toFixed(0)}%</span></div>
                    <div className="flex justify-between border-t border-border pt-1 mt-1"><span className="font-medium">Net Recovery</span><span className="font-bold text-text-primary">{formatCurrency(s.expected_net_recovery)}</span></div>
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-surface-lighter rounded-full h-1.5">
                      <div className="bg-primary h-1.5 rounded-full" style={{width: `${s.confidence * 100}%`}} />
                    </div>
                    <p className="text-xs text-text-muted mt-1">Confidence: {(s.confidence * 100).toFixed(0)}%</p>
                  </div>
                </button>
              ))}
            </div>

            {/* Explanation */}
            {selectedScenario && (
              <div className="mt-6 glass-card p-6">
                <h3 className="text-sm font-semibold text-primary mb-3">Why {actionLabels[selectedAction!] || selectedAction}?</h3>
                <p className="text-sm text-text-primary leading-relaxed">{selectedScenario.explanation}</p>
                {simulation.policy_decisions?.[selectedAction!] && (
                  <div className="mt-3 flex items-center gap-2">
                    <span className={clsx('text-xs font-medium px-2 py-1 rounded', simulation.policy_decisions[selectedAction!].approved ? 'bg-accent/10 text-accent' : 'bg-danger/10 text-danger')}>
                      Policy: {simulation.policy_decisions[selectedAction!].approved ? 'Approved' : 'Rejected'}
                    </span>
                    <span className="text-xs text-text-muted">{simulation.policy_decisions[selectedAction!].reason}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
