import React from 'react';

interface CardProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, style }) => (
  <div style={{
    background: '#1e293b',
    borderRadius: 12,
    border: '1px solid #334155',
    padding: '20px 24px',
    ...style,
  }}>
    {children}
  </div>
);

interface StatCardProps {
  label: string;
  value: string | number;
  icon: string;
  color?: string;
  subtext?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, icon, color = '#6366f1', subtext }) => (
  <Card>
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
      <div>
        <div style={{ color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>{label}</div>
        <div style={{ color: '#f1f5f9', fontSize: 28, fontWeight: 700 }}>{value}</div>
        {subtext && <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>{subtext}</div>}
      </div>
      <div style={{
        width: 44, height: 44, borderRadius: 10,
        background: `${color}22`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 20,
      }}>
        {icon}
      </div>
    </div>
  </Card>
);

interface BadgeProps {
  label: string;
  variant: 'high' | 'medium' | 'low' | 'info' | 'success' | 'warning';
}

const BADGE_COLORS: Record<string, { bg: string; text: string }> = {
  high: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444' },
  medium: { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
  low: { bg: 'rgba(34,197,94,0.15)', text: '#22c55e' },
  info: { bg: 'rgba(99,102,241,0.15)', text: '#6366f1' },
  success: { bg: 'rgba(34,197,94,0.15)', text: '#22c55e' },
  warning: { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b' },
};

export const Badge: React.FC<BadgeProps> = ({ label, variant }) => {
  const colors = BADGE_COLORS[variant] || BADGE_COLORS.info;
  return (
    <span style={{
      padding: '2px 10px',
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 600,
      background: colors.bg,
      color: colors.text,
      display: 'inline-block',
    }}>
      {label}
    </span>
  );
};

interface LoadingProps { text?: string }
export const Loading: React.FC<LoadingProps> = ({ text = 'Loading...' }) => (
  <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
    <div style={{ fontSize: 24, marginBottom: 8 }}>⏳</div>
    <div>{text}</div>
  </div>
);

interface ErrorDisplayProps { message: string; onRetry?: () => void }
export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message, onRetry }) => (
  <div style={{
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    padding: '16px 20px',
    color: '#ef4444',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  }}>
    <span style={{ fontSize: 18 }}>⚠️</span>
    <div style={{ flex: 1 }}>{message}</div>
    {onRetry && (
      <button onClick={onRetry} style={{
        background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)',
        color: '#ef4444', borderRadius: 6, padding: '4px 12px', cursor: 'pointer', fontSize: 13,
      }}>
        Retry
      </button>
    )}
  </div>
);

interface PageHeaderProps { title: string; subtitle?: string; action?: React.ReactNode }
export const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, action }) => (
  <div style={{ marginBottom: 28, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
    <div>
      <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>{title}</h1>
      {subtitle && <p style={{ margin: '6px 0 0', color: '#64748b', fontSize: 14 }}>{subtitle}</p>}
    </div>
    {action}
  </div>
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

const BTN_STYLES: Record<string, React.CSSProperties> = {
  primary: { background: '#6366f1', color: '#fff', border: '1px solid #6366f1' },
  secondary: { background: '#1e293b', color: '#94a3b8', border: '1px solid #334155' },
  danger: { background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' },
  ghost: { background: 'transparent', color: '#94a3b8', border: '1px solid transparent' },
};

const BTN_SIZE: Record<string, React.CSSProperties> = {
  sm: { padding: '6px 12px', fontSize: 12 },
  md: { padding: '8px 16px', fontSize: 14 },
  lg: { padding: '12px 24px', fontSize: 15 },
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary', size = 'md', loading, children, disabled, style, ...props
}) => (
  <button
    disabled={disabled || loading}
    style={{
      ...BTN_STYLES[variant],
      ...BTN_SIZE[size],
      borderRadius: 8,
      cursor: disabled || loading ? 'not-allowed' : 'pointer',
      fontWeight: 500,
      transition: 'opacity 0.15s',
      opacity: disabled || loading ? 0.6 : 1,
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      ...style,
    }}
    {...props}
  >
    {loading && <span>⏳</span>}
    {children}
  </button>
);

export const Divider: React.FC = () => (
  <hr style={{ border: 'none', borderTop: '1px solid #334155', margin: '16px 0' }} />
);
