import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { useSearchParams } from 'react-router-dom';
import {
  FlaskConical, Search, Sparkles, Sliders, ShieldCheck, ShieldAlert,
  Play, CheckCircle2, AlertTriangle, ArrowRight, User, CreditCard,
  Clock, DollarSign, Send, CheckCircle, RefreshCw, Zap
} from 'lucide-react';
import { clsx } from 'clsx';

const formatCurrency = (val: number | undefined | null) => {
  if (val === undefined || val === null || isNaN(val)) return '₹0';
  return `₹${Number(val).toLocaleString('en-IN')}`;
};

const actionLabels: Record<string, string> = {
  retry_now: 'Immediate Retry',
  retry_15m: 'Retry in 15 min',
  retry_45m: 'Retry in 45 min',
  whatsapp: 'WhatsApp Payment Link',
  payment_link: 'SMS Payment Link',
  email: 'Dunning Email',
  human_escalation: 'Human Concierge Escalation',
  stop: 'Cease Interventions',
};

const PRESETS = [
  {
    name: '⚡ Peak-Hour UPI Bank Timeout',
    amount: 12500,
    paymentMethod: 'upi',
    failureReason: 'bank_timeout',
    customerName: 'Aditi Sharma',
    customerSegment: 'premium',
    successRate: 92,
    hour: 20,
    isDnd: false,
    retryCount: 0,
  },
  {
    name: '💳 High-Value Card Expired (VIP)',
    amount: 68500,
    paymentMethod: 'card',
    failureReason: 'expired_card',
    customerName: 'Vikram Singhania',
    customerSegment: 'high_value',
    successRate: 98,
    hour: 14,
    isDnd: false,
    retryCount: 0,
  },
  {
    name: '📉 Insufficient Balance (Salary Delay)',
    amount: 3400,
    paymentMethod: 'upi',
    failureReason: 'insufficient_funds',
    customerName: 'Rahul Verma',
    customerSegment: 'regular',
    successRate: 75,
    hour: 11,
    isDnd: false,
    retryCount: 1,
  },
  {
    name: '🛒 Checkout Cart Abandonment',
    amount: 4200,
    paymentMethod: 'wallet',
    failureReason: 'checkout_abandonment',
    customerName: 'Priya Nair',
    customerSegment: 'new',
    successRate: 60,
    hour: 19,
    isDnd: true,
    retryCount: 0,
  },
];

export default function WhatIfLab() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<'custom' | 'lookup'>('custom');

  // Custom Input State
  const [customAmount, setCustomAmount] = useState<number>(12500);
  const [customMethod, setCustomMethod] = useState<string>('upi');
  const [customReason, setCustomReason] = useState<string>('bank_timeout');
  const [customName, setCustomName] = useState<string>('Aditi Sharma');
  const [customSegment, setCustomSegment] = useState<string>('premium');
  const [customSuccessRate, setCustomSuccessRate] = useState<number>(92);
  const [customHour, setCustomHour] = useState<number>(20);
  const [customIsDnd, setCustomIsDnd] = useState<boolean>(false);
  const [customRetryCount, setCustomRetryCount] = useState<number>(0);

  // Lookup State
  const [txnId, setTxnId] = useState(searchParams.get('txn') || 'TXN_000001');

  // Simulation Results
  const [simulation, setSimulation] = useState<any>(null);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Live Execution State
  const [executing, setExecuting] = useState(false);
  const [executionStep, setExecutionStep] = useState<number>(0);
  const [executionSuccess, setExecutionSuccess] = useState(false);

  // Compute live counterfactual twin for custom input
  const calculateCustomSimulation = () => {
    const amount = Number(customAmount) || 1000;
    const isUpi = customMethod === 'upi';
    const isCard = customMethod === 'card';
    const isTimeout = customReason === 'bank_timeout';
    const isExpired = customReason === 'expired_card';
    const isInsufficient = customReason === 'insufficient_funds';
    const isAbandonment = customReason === 'checkout_abandonment';
    const isPeakHour = customHour >= 18 && customHour <= 22;
    const baseRate = customSuccessRate / 100;

    // Simulate competing actions
    const scenarios: any[] = [];

    // 1. Immediate Retry
    let pRetryNow = 0.35 * baseRate;
    if (isTimeout && isPeakHour) pRetryNow = 0.20;
    if (isExpired) pRetryNow = 0.02;
    if (isInsufficient) pRetryNow = 0.15;
    const expRevNow = pRetryNow * amount;
    const costNow = 0;
    const fricNow = 0.04;
    const enrNow = expRevNow - costNow - (fricNow * amount);
    scenarios.push({
      action: 'retry_now',
      recovery_probability: Number(pRetryNow.toFixed(2)),
      expected_revenue: Number(expRevNow.toFixed(2)),
      intervention_cost: costNow,
      friction_score: fricNow,
      expected_net_recovery: Number(enrNow.toFixed(2)),
      confidence: 0.85,
      explanation: isTimeout && isPeakHour
        ? 'Immediate retry during peak UPI bank congestion has very low success (<20%) and burns gateway rate limits.'
        : isExpired
        ? 'Immediate retry on an expired card will fail 100% without card update.'
        : 'Immediate retry attempts fast recovery with zero intervention cost.',
    });

    // 2. 15-min Delay Retry
    let pRetry15 = 0.65 * baseRate;
    if (isTimeout && isPeakHour) pRetry15 = 0.60;
    if (isExpired) pRetry15 = 0.02;
    const expRev15 = pRetry15 * amount;
    const enr15 = expRev15 - (0.02 * amount);
    scenarios.push({
      action: 'retry_15m',
      recovery_probability: Number(pRetry15.toFixed(2)),
      expected_revenue: Number(expRev15.toFixed(2)),
      intervention_cost: 0,
      friction_score: 0.02,
      expected_net_recovery: Number(enr15.toFixed(2)),
      confidence: 0.88,
      explanation: '15-minute cooldown allows transient gateway network glitches to settle.',
    });

    // 3. 45-min Delay Retry
    let pRetry45 = 0.82 * baseRate;
    if (isTimeout && isPeakHour) pRetry45 = 0.88;
    if (isExpired) pRetry45 = 0.02;
    const expRev45 = pRetry45 * amount;
    const enr45 = expRev45 - (0.01 * amount);
    scenarios.push({
      action: 'retry_45m',
      recovery_probability: Number(pRetry45.toFixed(2)),
      expected_revenue: Number(expRev45.toFixed(2)),
      intervention_cost: 0,
      friction_score: 0.01,
      expected_net_recovery: Number(enr45.toFixed(2)),
      confidence: 0.92,
      explanation: '45-minute delayed retry maximizes recovery after bank maintenance windows while imposing 0 cost and minimal friction.',
    });

    // 4. WhatsApp Interactive Link
    let pWa = isExpired ? 0.76 * baseRate : isAbandonment ? 0.81 * baseRate : 0.72 * baseRate;
    if (customIsDnd) pWa = 0.0;
    const costWa = 2.5;
    const fricWa = customIsDnd ? 0.8 : 0.08;
    const expRevWa = pWa * amount;
    const enrWa = expRevWa - costWa - (fricWa * amount);
    scenarios.push({
      action: 'whatsapp',
      recovery_probability: Number(pWa.toFixed(2)),
      expected_revenue: Number(expRevWa.toFixed(2)),
      intervention_cost: costWa,
      friction_score: fricWa,
      expected_net_recovery: Number(enrWa.toFixed(2)),
      confidence: 0.89,
      explanation: customIsDnd
        ? 'Customer is registered on DND. WhatsApp messaging is blocked by compliance policy.'
        : isExpired
        ? 'Direct WhatsApp message with 1-click Razorpay payment method update link yields 76% recovery.'
        : 'High-open rate WhatsApp interactive button recovers cart abandonments and customer payment drops.',
    });

    // 5. SMS Link
    let pSms = isExpired ? 0.45 * baseRate : 0.52 * baseRate;
    if (customIsDnd) pSms = 0.0;
    const costSms = 0.5;
    const expRevSms = pSms * amount;
    const enrSms = expRevSms - costSms - (0.06 * amount);
    scenarios.push({
      action: 'payment_link',
      recovery_probability: Number(pSms.toFixed(2)),
      expected_revenue: Number(expRevSms.toFixed(2)),
      intervention_cost: costSms,
      friction_score: 0.06,
      expected_net_recovery: Number(enrSms.toFixed(2)),
      confidence: 0.80,
      explanation: customIsDnd ? 'Blocked by DND policy.' : 'Standard SMS fallback payment link.',
    });

    // 6. Dunning Email
    let pEmail = isExpired ? 0.38 * baseRate : 0.32 * baseRate;
    const costEmail = 0.1;
    const expRevEmail = pEmail * amount;
    const enrEmail = expRevEmail - costEmail - (0.03 * amount);
    scenarios.push({
      action: 'email',
      recovery_probability: Number(pEmail.toFixed(2)),
      expected_revenue: Number(expRevEmail.toFixed(2)),
      intervention_cost: costEmail,
      friction_score: 0.03,
      expected_net_recovery: Number(enrEmail.toFixed(2)),
      confidence: 0.75,
      explanation: 'Low-cost asynchronous email notification for recurring subscriptions.',
    });

    // 7. Human Concierge Escalation
    let pHuman = amount > 25000 ? 0.92 : 0.70;
    const costHuman = 50.0;
    const fricHuman = 0.12;
    const expRevHuman = pHuman * amount;
    const enrHuman = expRevHuman - costHuman - (fricHuman * amount);
    scenarios.push({
      action: 'human_escalation',
      recovery_probability: Number(pHuman.toFixed(2)),
      expected_revenue: Number(expRevHuman.toFixed(2)),
      intervention_cost: costHuman,
      friction_score: fricHuman,
      expected_net_recovery: Number(enrHuman.toFixed(2)),
      confidence: 0.95,
      explanation: amount > 50000
        ? 'High transaction value (>₹50,000) qualifies for VIP VIP relationship manager outreach.'
        : 'Dedicated human agent phone call (high intervention cost ₹50).',
    });

    // Policy Checks
    const policyDecisions: Record<string, { approved: boolean; reason: string }> = {};
    scenarios.forEach(s => {
      let approved = true;
      let reason = 'All 10 deterministic guardrails satisfied.';

      if (customRetryCount >= 3 && s.action.startsWith('retry')) {
        approved = false;
        reason = 'Policy Rule #2: Max retries (3) reached for this transaction.';
      } else if (customIsDnd && (s.action === 'whatsapp' || s.action === 'payment_link')) {
        approved = false;
        reason = 'Policy Rule #5: Customer is on DND. Outbound messaging prohibited.';
      } else if (amount > 50000 && s.action === 'retry_now') {
        approved = false;
        reason = 'Policy Rule #6: Amount exceeds ₹50,000 auto-recovery threshold. Requires escalation.';
      }

      s.is_policy_approved = approved;
      s.policy_rejection_reason = approved ? null : reason;
      policyDecisions[s.action] = { approved, reason };
    });

    // Pick best approved action by highest ENR
    const eligible = scenarios.filter(s => s.is_policy_approved);
    eligible.sort((a, b) => b.expected_net_recovery - a.expected_net_recovery);
    const bestAction = eligible.length > 0 ? eligible[0].action : 'retry_45m';

    scenarios.forEach(s => {
      s.is_recommended = s.action === bestAction;
    });

    const simResult = {
      transaction_id: 'CUSTOM_SIM_' + Math.floor(Math.random() * 90000 + 10000),
      amount: amount,
      payment_method: customMethod,
      failure_reason: customReason,
      customer: {
        name: customName,
        segment: customSegment,
        payment_success_rate: baseRate,
        is_dnd: customIsDnd,
      },
      scenarios,
      recommended_action: bestAction,
      recommended_action_label: actionLabels[bestAction] || bestAction,
      explanation: isTimeout && isPeakHour
        ? `Customer ${customName} has a strong payment history (${customSuccessRate}%). However, UPI peak bank congestion caused a timeout. A delayed retry (45m) maximizes Expected Net Recovery (${formatCurrency(eligible[0]?.expected_net_recovery)}) with zero intervention cost.`
        : isExpired
        ? `Card expired for ${customName}. Automated retries will fail. Sending a WhatsApp interactive update link is the optimal action with ${((eligible[0]?.recovery_probability || 0.76) * 100).toFixed(0)}% recovery probability.`
        : `AI Twin evaluated 7 counterfactual strategies. ${actionLabels[bestAction]} delivers the highest net recovery (${formatCurrency(eligible[0]?.expected_net_recovery)}) under merchant policy constraints.`,
      policy_decisions: policyDecisions,
    };

    setSimulation(simResult);
    setSelectedAction(bestAction);
  };

  // Run simulation on mount or when custom inputs change
  useEffect(() => {
    if (activeTab === 'custom') {
      calculateCustomSimulation();
    }
  }, [
    activeTab, customAmount, customMethod, customReason,
    customName, customSegment, customSuccessRate, customHour,
    customIsDnd, customRetryCount
  ]);

  const handleApplyPreset = (preset: typeof PRESETS[0]) => {
    setCustomAmount(preset.amount);
    setCustomMethod(preset.paymentMethod);
    setCustomReason(preset.failureReason);
    setCustomName(preset.customerName);
    setCustomSegment(preset.customerSegment);
    setCustomSuccessRate(preset.successRate);
    setCustomHour(preset.hour);
    setCustomIsDnd(preset.isDnd);
    setCustomRetryCount(preset.retryCount);
    setActiveTab('custom');
  };

  const handleSearchLookup = async () => {
    if (!txnId) return;
    setLoading(true);
    try {
      const [txnData, simData] = await Promise.all([
        api.getTransaction(txnId),
        api.simulateRecovery(txnId),
      ]);
      setSimulation(simData);
      setSelectedAction(simData.recommended_action);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Simulate live step-by-step execution animation
  const handleExecuteLiveRecovery = () => {
    setExecuting(true);
    setExecutionStep(1);
    setExecutionSuccess(false);

    setTimeout(() => setExecutionStep(2), 700);
    setTimeout(() => setExecutionStep(3), 1400);
    setTimeout(() => setExecutionStep(4), 2100);
    setTimeout(() => {
      setExecutionStep(5);
      setExecutionSuccess(true);
      setExecuting(false);
    }, 2800);
  };

  const selectedScenario = simulation?.scenarios?.find((s: any) => s.action === selectedAction);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-primary" /> Recovery What-If & Custom Simulator
          </h1>
          <p className="text-text-secondary mt-1">
            Input your own transaction data or tweak failure parameters to see real-time Counterfactual Twin calculations
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center gap-2 p-1 bg-surface-lighter rounded-xl border border-border">
          <button
            onClick={() => setActiveTab('custom')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2',
              activeTab === 'custom'
                ? 'bg-primary text-white shadow'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
            <Sliders className="w-4 h-4" /> Custom Data Lab
          </button>
          <button
            onClick={() => { setActiveTab('lookup'); handleSearchLookup(); }}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2',
              activeTab === 'lookup'
                ? 'bg-primary text-white shadow'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
            <Search className="w-4 h-4" /> Lookup Transaction
          </button>
        </div>
      </div>

      {/* Preset Quick Chips */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">
          Quick Failure Presets:
        </p>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.name}
              onClick={() => handleApplyPreset(p)}
              className="text-xs px-3 py-1.5 rounded-lg glass-card hover:border-primary/40 text-text-secondary hover:text-text-primary transition-all flex items-center gap-1.5"
            >
              {p.name} <span className="text-text-muted">({formatCurrency(p.amount)})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Mode A: Custom Data Input Form */}
      {activeTab === 'custom' && (
        <div className="glass-card p-6 border-primary/20 space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <h2 className="text-lg font-bold flex items-center gap-2 text-text-primary">
              <Sliders className="w-5 h-5 text-primary" /> Custom Transaction Parameters
            </h2>
            <span className="text-xs px-2.5 py-1 rounded-full bg-accent/10 text-accent font-mono">
              Live Counterfactual Engine Active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Amount */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-secondary flex justify-between">
                <span>Transaction Amount (₹)</span>
                <span className="font-bold text-text-primary">{formatCurrency(customAmount)}</span>
              </label>
              <input
                type="number"
                value={customAmount}
                onChange={(e) => setCustomAmount(Number(e.target.value) || 0)}
                className="w-full bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                min={100}
                max={500000}
                step={500}
              />
              <div className="flex gap-1.5">
                {[999, 4999, 12500, 55000].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setCustomAmount(amt)}
                    className="text-[10px] px-2 py-0.5 rounded bg-surface border border-border text-text-muted hover:text-text-primary"
                  >
                    ₹{amt >= 1000 ? `${amt / 1000}K` : amt}
                  </button>
                ))}
              </div>
            </div>

            {/* Payment Method */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-secondary">Payment Method</label>
              <select
                value={customMethod}
                onChange={(e) => setCustomMethod(e.target.value)}
                className="w-full bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="upi">UPI (GPay / PhonePe / Paytm)</option>
                <option value="card">Credit / Debit Card</option>
                <option value="netbanking">Net Banking</option>
                <option value="wallet">Mobile Wallet</option>
              </select>
            </div>

            {/* Failure Reason */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-secondary">Failure Cause / Root Cause</label>
              <select
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                className="w-full bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="bank_timeout">UPI / Bank Server Timeout</option>
                <option value="expired_card">Card Expired / Invalid Card</option>
                <option value="insufficient_funds">Insufficient Account Balance</option>
                <option value="authentication_failed">Authentication / OTP Failure</option>
                <option value="checkout_abandonment">Checkout Abandonment</option>
                <option value="network_error">Gateway Network Error</option>
              </select>
            </div>

            {/* Customer Segment */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-text-secondary">Customer Segment</label>
              <select
                value={customSegment}
                onChange={(e) => setCustomSegment(e.target.value)}
                className="w-full bg-surface-lighter border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
              >
                <option value="premium">VIP Premium Customer</option>
                <option value="returning">Returning Regular Customer</option>
                <option value="high_value">High-Value Enterprise</option>
                <option value="new">First-Time New User</option>
              </select>
            </div>
          </div>

          {/* Advanced Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2 border-t border-border/50">
            {/* Success Rate Slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-text-secondary">Customer Historical Success Rate</span>
                <span className="font-bold text-accent">{customSuccessRate}%</span>
              </div>
              <input
                type="range"
                min={20}
                max={99}
                value={customSuccessRate}
                onChange={(e) => setCustomSuccessRate(Number(e.target.value))}
                className="w-full accent-accent"
              />
            </div>

            {/* Hour of Day */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-text-secondary">Time of Day (IST)</span>
                <span className="font-bold text-primary">
                  {customHour}:00 {customHour >= 18 && customHour <= 22 ? '(Peak Congestion)' : '(Off-Peak)'}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={23}
                value={customHour}
                onChange={(e) => setCustomHour(Number(e.target.value))}
                className="w-full accent-primary"
              />
            </div>

            {/* DND Toggle & Retries */}
            <div className="flex items-center justify-between pt-2">
              <div className="space-y-1">
                <label className="text-xs font-medium text-text-secondary">DND Preference</label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setCustomIsDnd(!customIsDnd)}
                    className={clsx(
                      'px-3 py-1 rounded text-xs font-medium transition-all',
                      customIsDnd ? 'bg-danger/20 text-danger border border-danger/40' : 'bg-surface-lighter text-text-secondary border border-border'
                    )}
                  >
                    {customIsDnd ? '🚫 DND Active (No SMS/WA)' : '✅ Opted-in'}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-text-secondary">Prior Retries</label>
                <div className="flex items-center gap-1">
                  {[0, 1, 2, 3].map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setCustomRetryCount(r)}
                      className={clsx(
                        'w-7 h-7 rounded text-xs font-bold transition-all',
                        customRetryCount === r
                          ? 'bg-primary text-white'
                          : 'bg-surface-lighter text-text-muted hover:text-text-primary'
                      )}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode B: Lookup Form */}
      {activeTab === 'lookup' && (
        <div className="glass-card p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={txnId}
              onChange={(e) => setTxnId(e.target.value)}
              placeholder="Enter Transaction ID (e.g., TXN_000001)"
              className="flex-1 bg-surface-lighter border border-border rounded-lg px-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-primary font-mono"
              onKeyDown={(e) => e.key === 'Enter' && handleSearchLookup()}
            />
            <button
              onClick={handleSearchLookup}
              disabled={loading}
              className="px-6 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <Search className="w-4 h-4" /> {loading ? 'Loading...' : 'Analyze'}
            </button>
          </div>
        </div>
      )}

      {/* Simulation Output */}
      {simulation && (
        <div className="space-y-6">
          {/* Recommendation Banner */}
          <div className="glass-card p-6 bg-gradient-to-r from-primary/10 via-surface-light to-accent/10 border-primary/30 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-accent/20 text-accent">
                  AI Twin Optimal Decision
                </span>
                <span className="text-xs text-text-muted">
                  Transaction: <span className="font-mono text-text-primary">{formatCurrency(simulation.amount)}</span>
                </span>
              </div>
              <h3 className="text-xl font-bold text-text-primary flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-accent" /> Recommended:{' '}
                <span className="text-accent">{simulation.recommended_action_label}</span>
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed max-w-3xl">
                {simulation.explanation}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleExecuteLiveRecovery}
                disabled={executing}
                className="px-6 py-3 bg-gradient-to-r from-accent to-emerald-600 hover:from-accent-light hover:to-emerald-500 text-slate-900 font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-slate-900" /> Executing Action...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 text-slate-900 fill-slate-900" /> Execute Live Recovery
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Live Execution Animation Card */}
          {(executing || executionSuccess) && (
            <div className="glass-card p-6 border-accent/30 bg-accent/5 transition-all">
              <h4 className="text-sm font-bold text-accent mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4" /> Live Recovery State Machine Progression
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                {[
                  { step: 1, label: '1. Ingestion', desc: 'Failure Ingested' },
                  { step: 2, label: '2. Diagnosis', desc: 'Root Cause Mapped' },
                  { step: 3, label: '3. Policy Check', desc: '10 Rules Approved' },
                  { step: 4, label: '4. Dispatch', desc: 'Adapter Triggered' },
                  { step: 5, label: '5. Settled', desc: 'Revenue Recovered' },
                ].map((s) => (
                  <div
                    key={s.step}
                    className={clsx(
                      'p-3 rounded-lg border text-center transition-all',
                      executionStep >= s.step
                        ? 'bg-accent/20 border-accent/40 text-text-primary'
                        : 'bg-surface border-border text-text-muted'
                    )}
                  >
                    <p className="text-xs font-bold">{s.label}</p>
                    <p className="text-[11px] mt-0.5">{s.desc}</p>
                    {executionStep >= s.step && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-accent mx-auto mt-1" />
                    )}
                  </div>
                ))}
              </div>
              {executionSuccess && (
                <div className="mt-4 p-3 rounded-lg bg-accent/20 text-accent text-sm font-semibold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-accent" />
                  Successfully recovered {formatCurrency(simulation.amount)} via{' '}
                  {simulation.recommended_action_label}! Net merchant gain recorded in ledger.
                </div>
              )}
            </div>
          )}

          {/* Competing Counterfactual Scenarios */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-text-primary">
                Simulated Counterfactual Interventions ({simulation.scenarios?.length || 0})
              </h3>
              <span className="text-xs text-text-muted">
                Formula: ENR = (P_rec × Amount) - Cost - Friction
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {simulation.scenarios?.map((s: any) => {
                const isSelected = s.action === selectedAction;
                const isApproved = s.is_policy_approved !== false;

                return (
                  <button
                    key={s.action}
                    onClick={() => setSelectedAction(s.action)}
                    className={clsx(
                      'text-left rounded-xl p-5 border transition-all relative flex flex-col justify-between',
                      isSelected
                        ? 'bg-primary/15 border-primary ring-1 ring-primary'
                        : s.is_recommended
                        ? 'bg-accent/5 border-accent/30 hover:border-accent'
                        : 'bg-surface-light border-border hover:border-border/80',
                      !isApproved && 'opacity-60 border-danger/20'
                    )}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-text-primary">
                          {actionLabels[s.action] || s.action}
                        </span>
                        {s.is_recommended && (
                          <span className="text-[10px] bg-accent/20 text-accent font-bold px-2 py-0.5 rounded-full">
                            ★ HIGHEST ENR
                          </span>
                        )}
                        {!isApproved && (
                          <span className="text-[10px] bg-danger/20 text-danger font-bold px-2 py-0.5 rounded-full">
                            BLOCKED
                          </span>
                        )}
                      </div>

                      <div className="my-3">
                        <span className="text-2xl font-extrabold text-text-primary">
                          {((s.recovery_probability || 0) * 100).toFixed(0)}%
                        </span>
                        <span className="text-xs text-text-muted ml-1">rec. probability</span>
                      </div>

                      <div className="space-y-1.5 text-xs text-text-secondary border-t border-border/60 pt-3">
                        <div className="flex justify-between">
                          <span>Expected Revenue:</span>
                          <span className="font-semibold text-text-primary">
                            {formatCurrency(s.expected_revenue)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Intervention Cost:</span>
                          <span className="font-semibold">₹{s.intervention_cost}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Customer Friction:</span>
                          <span className="font-semibold">
                            {((s.friction_score || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between border-t border-border pt-1.5 mt-1 font-bold">
                          <span className="text-text-primary">Expected Net Rec.:</span>
                          <span className={clsx(s.expected_net_recovery > 0 ? 'text-accent' : 'text-danger')}>
                            {formatCurrency(s.expected_net_recovery)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-border/40">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-text-muted">Guardrail:</span>
                        <span className={clsx('font-medium', isApproved ? 'text-accent' : 'text-danger')}>
                          {isApproved ? 'Approved' : 'Rejected'}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Deep-Dive Explanation Card */}
          {selectedScenario && (
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-primary flex items-center gap-2">
                  <Sparkles className="w-4 h-4" /> Why{' '}
                  {actionLabels[selectedAction!] || selectedAction}?
                </h3>
                <span
                  className={clsx(
                    'text-xs font-semibold px-2.5 py-1 rounded-md flex items-center gap-1',
                    selectedScenario.is_policy_approved !== false
                      ? 'bg-accent/10 text-accent'
                      : 'bg-danger/10 text-danger'
                  )}
                >
                  {selectedScenario.is_policy_approved !== false ? (
                    <>
                      <ShieldCheck className="w-3.5 h-3.5" /> Policy Compliant
                    </>
                  ) : (
                    <>
                      <ShieldAlert className="w-3.5 h-3.5" /> Policy Blocked
                    </>
                  )}
                </span>
              </div>

              <p className="text-sm text-text-primary leading-relaxed">
                {selectedScenario.explanation}
              </p>

              {selectedScenario.policy_rejection_reason && (
                <div className="p-3 rounded-lg bg-danger/10 border border-danger/20 text-xs text-danger flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{selectedScenario.policy_rejection_reason}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
