import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  label: string;
  value: string;
  change?: number;
  icon?: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning';
}

const variantStyles = {
  default: 'text-text-primary',
  success: 'text-accent',
  danger: 'text-danger',
  warning: 'text-warning',
};

export default function KPICard({ label, value, change, icon, variant = 'default' }: KPICardProps) {
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between mb-3">
        <span className="kpi-label">{label}</span>
        {icon && <span className="text-text-muted">{icon}</span>}
      </div>
      <div className={clsx('kpi-value', variantStyles[variant])}>{value}</div>
      {change !== undefined && (
        <div className="flex items-center gap-1 mt-2">
          {change > 0 ? (
            <TrendingUp className="w-3 h-3 text-accent" />
          ) : change < 0 ? (
            <TrendingDown className="w-3 h-3 text-danger" />
          ) : (
            <Minus className="w-3 h-3 text-text-muted" />
          )}
          <span
            className={clsx(
              'text-xs font-medium',
              change > 0 ? 'text-accent' : change < 0 ? 'text-danger' : 'text-text-muted'
            )}
          >
            {change > 0 ? '+' : ''}
            {change.toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  );
}
