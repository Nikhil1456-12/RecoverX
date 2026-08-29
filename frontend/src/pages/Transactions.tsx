import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Link } from 'react-router-dom';
import { Search, Filter, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { clsx } from 'clsx';

const statusColors: Record<string, string> = {
  success: 'bg-accent/10 text-accent border-accent/20',
  failed: 'bg-danger/10 text-danger border-danger/20',
  recovered: 'bg-primary/10 text-primary border-primary/20',
  pending: 'bg-warning/10 text-warning border-warning/20',
};

const formatCurrency = (val: number | undefined | null) => {
  if (val === undefined || val === null || isNaN(val)) return '₹0';
  return `₹${val.toLocaleString('en-IN', { minimumFractionDigits: 0 })}`;
};

export default function Transactions() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [status, setStatus] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [failureReason, setFailureReason] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: page.toString(), page_size: pageSize.toString() };
      if (status) params.status = status;
      if (paymentMethod) params.payment_method = paymentMethod;
      if (failureReason) params.failure_reason = failureReason;
      const data = await api.getTransactions(params);
      setTransactions(data.transactions);
      setTotal(data.total);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTransactions(); }, [page, status, paymentMethod, failureReason]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Transactions</h1>
          <p className="text-text-secondary mt-1">{total.toLocaleString()} total transactions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <Filter className="w-4 h-4 text-text-muted" />
          <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }} className="bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary">
            <option value="">All Status</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="recovered">Recovered</option>
          </select>
          <select value={paymentMethod} onChange={e => { setPaymentMethod(e.target.value); setPage(1); }} className="bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary">
            <option value="">All Methods</option>
            <option value="upi">UPI</option>
            <option value="card">Card</option>
            <option value="netbanking">Netbanking</option>
            <option value="wallet">Wallet</option>
          </select>
          <select value={failureReason} onChange={e => { setFailureReason(e.target.value); setPage(1); }} className="bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary">
            <option value="">All Failure Reasons</option>
            <option value="bank_timeout">Bank Timeout</option>
            <option value="insufficient_funds">Insufficient Funds</option>
            <option value="expired_card">Expired Card</option>
            <option value="network_error">Network Error</option>
            <option value="bank_decline">Bank Decline</option>
            <option value="checkout_abandonment">Checkout Abandonment</option>
            <option value="authentication_failure">Auth Failure</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Transaction ID</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Customer</th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Amount</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Method</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Status</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Failure Reason</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider">Date</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-text-muted uppercase tracking-wider"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="text-center py-12 text-text-secondary">Loading...</td></tr>
            ) : transactions.map((txn) => (
              <tr key={txn.id} className="border-b border-border/50 hover:bg-surface-light/50 transition-colors">
                <td className="px-4 py-3 text-sm font-mono">{txn.id}</td>
                <td className="px-4 py-3">
                  <div>
                    <p className="text-sm">{txn.customer_name || txn.customer_id}</p>
                    <p className="text-xs text-text-muted">{txn.customer_segment}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-right font-medium">{formatCurrency(txn.amount)}</td>
                <td className="px-4 py-3 text-sm uppercase">{txn.payment_method}</td>
                <td className="px-4 py-3">
                  <span className={clsx('px-2 py-1 rounded-md text-xs font-medium border', statusColors[txn.status] || 'bg-surface-lighter text-text-secondary')}>
                    {txn.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-text-secondary">{txn.failure_reason?.replace(/_/g, ' ') || '—'}</td>
                <td className="px-4 py-3 text-sm text-text-secondary">{new Date(txn.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <Link to={`/transactions/${txn.id}`} className="text-primary hover:text-primary-light">
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-text-secondary">Showing {((page-1)*pageSize)+1}–{Math.min(page*pageSize, total)} of {total}</p>
        <div className="flex items-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="p-2 rounded-lg hover:bg-surface-light disabled:opacity-30">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm text-text-secondary">Page {page} of {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page === totalPages} className="p-2 rounded-lg hover:bg-surface-light disabled:opacity-30">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
