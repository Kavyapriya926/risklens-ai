import React from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid, Legend,
} from 'recharts';
import { getDashboardStats, getDashboardCharts } from '../api/client';
import { useApi } from '../hooks/useApi';
import { StatCard, Card, Loading, ErrorDisplay, PageHeader } from '../components/common/Card';

const RISK_COLORS = { low: '#22c55e', medium: '#f59e0b', high: '#ef4444' };
const PIE_COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6'];

export const Dashboard: React.FC = () => {
  const stats = useApi(getDashboardStats, []);
  const charts = useApi(getDashboardCharts, []);

  if (stats.loading) return <Loading text="Loading dashboard..." />;
  if (stats.error) return <ErrorDisplay message={stats.error} onRetry={stats.refetch} />;

  const s = stats.data!;

  return (
    <div>
      <PageHeader
        title="Risk Dashboard"
        subtitle="Real-time overview of fraud detection activity"
        action={
          <button onClick={stats.refetch} style={{
            background: '#1e293b', border: '1px solid #334155',
            color: '#94a3b8', borderRadius: 8, padding: '8px 14px',
            cursor: 'pointer', fontSize: 13,
          }}>
            🔄 Refresh
          </button>
        }
      />

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
        <StatCard label="Transactions Analyzed" value={s.total_transactions.toLocaleString()} icon="📋" color="#6366f1" subtext={`${s.transactions_today} today`} />
        <StatCard label="High Risk" value={s.high_risk_count.toLocaleString()} icon="🚨" color="#ef4444" subtext={`${s.high_risk_today} today`} />
        <StatCard label="Pending Investigations" value={s.pending_investigations.toLocaleString()} icon="🕵️" color="#f59e0b" />
        <StatCard label="Fraud Rate" value={`${s.fraud_rate_pct.toFixed(1)}%`} icon="🎯" color="#8b5cf6" subtext="Confirmed cases" />
        <StatCard label="Avg Risk Score" value={s.avg_risk_score.toFixed(1)} icon="📊" color="#06b6d4" subtext="Out of 100" />
      </div>

      {charts.loading ? (
        <Loading text="Loading charts..." />
      ) : charts.error ? (
        <ErrorDisplay message={charts.error} />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Daily Trends */}
          <Card style={{ gridColumn: '1 / -1' }}>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Investigation Trends — Last 14 Days</h3>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={charts.data?.daily_trends || []}>
                <defs>
                  <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Legend />
                <Area type="monotone" dataKey="total" stroke="#6366f1" fill="url(#totalGrad)" name="Total" strokeWidth={2} />
                <Area type="monotone" dataKey="high_risk" stroke="#ef4444" fill="url(#highGrad)" name="High Risk" strokeWidth={2} />
                <Area type="monotone" dataKey="reviewed" stroke="#22c55e" fill="none" name="Reviewed" strokeWidth={2} strokeDasharray="4 2" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          {/* Risk Distribution Pie */}
          <Card>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={charts.data?.risk_distribution || []}
                  dataKey="count"
                  nameKey="range"
                  cx="50%" cy="50%"
                  outerRadius={80}
                  label={({ range, percentage }) => `${range}: ${percentage}%`}
                  labelLine={false}
                >
                  {(charts.data?.risk_distribution || []).map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* Category Breakdown */}
          <Card>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Top Categories by Volume</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={(charts.data?.category_breakdown || []).slice(0, 6)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="category" stroke="#64748b" tick={{ fontSize: 11 }} width={110} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Bar dataKey="total" fill="#6366f1" name="Total" radius={[0, 4, 4, 0]} />
                <Bar dataKey="high_risk" fill="#ef4444" name="High Risk" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Risk Level Summary */}
          <Card style={{ gridColumn: '1 / -1' }}>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Risk Level Breakdown</h3>
            <div style={{ display: 'flex', gap: 12 }}>
              {(['high', 'medium', 'low'] as const).map((level) => {
                const count = level === 'high' ? s.high_risk_count : level === 'medium' ? s.medium_risk_count : s.low_risk_count;
                const pct = s.total_transactions > 0 ? (count / s.total_transactions * 100).toFixed(1) : '0';
                const color = RISK_COLORS[level];
                return (
                  <div key={level} style={{ flex: 1, background: '#0f172a', borderRadius: 10, padding: '16px 20px', border: `1px solid ${color}33` }}>
                    <div style={{ color, fontSize: 13, fontWeight: 600, textTransform: 'uppercase', marginBottom: 6 }}>{level} risk</div>
                    <div style={{ color: '#f1f5f9', fontSize: 28, fontWeight: 700 }}>{count.toLocaleString()}</div>
                    <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>{pct}% of total</div>
                    <div style={{
                      marginTop: 10, height: 4, borderRadius: 2,
                      background: '#334155',
                    }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.5s' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
