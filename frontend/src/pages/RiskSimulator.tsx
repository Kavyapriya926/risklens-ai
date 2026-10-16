import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { runSimulation, getCurrentThresholds } from '../api/client';
import type { SimulatorInput, SimulatorResult } from '../types';
import { Card, Button, Loading, ErrorDisplay, PageHeader } from '../components/common/Card';
import { useApi } from '../hooks/useApi';

const DEFAULT_CONFIG: SimulatorInput = {
  low_threshold: 40,
  high_threshold: 70,
  review_cost_per_case: 500,
  fraud_loss_per_case: 15000,
};

export const RiskSimulator: React.FC = () => {
  const [config, setConfig] = useState<SimulatorInput>(DEFAULT_CONFIG);
  const [result, setResult] = useState<SimulatorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: currentThresholds } = useApi(getCurrentThresholds, []);

  const handleSimulate = async () => {
    if (config.low_threshold >= config.high_threshold) {
      setError('Low threshold must be less than high threshold');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const r = await runSimulation(config);
      setResult(r);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
    padding: '8px 12px', color: '#f1f5f9', fontSize: 14, outline: 'none', width: '100%',
    boxSizing: 'border-box',
  };

  const MetricDiff: React.FC<{ label: string; current: number; baseline: number; higherIsBetter?: boolean; format?: 'pct' | 'currency' | 'count' }> = ({
    label, current, baseline, higherIsBetter = true, format = 'count',
  }) => {
    const diff = current - baseline;
    const isImproved = higherIsBetter ? diff > 0 : diff < 0;
    const fmt = (v: number) =>
      format === 'pct' ? `${(v * 100).toFixed(1)}%` :
      format === 'currency' ? `₹${v.toLocaleString('en-IN')}` :
      v.toLocaleString();
    return (
      <div style={{ padding: '10px 14px', background: '#0f172a', borderRadius: 8 }}>
        <div style={{ color: '#64748b', fontSize: 12, marginBottom: 4 }}>{label}</div>
        <div style={{ color: '#f1f5f9', fontSize: 20, fontWeight: 700 }}>{fmt(current)}</div>
        {diff !== 0 && (
          <div style={{ fontSize: 12, color: isImproved ? '#22c55e' : '#ef4444', marginTop: 2 }}>
            {diff > 0 ? '▲' : '▼'} {fmt(Math.abs(diff))} vs baseline
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <PageHeader
        title="Risk Simulator"
        subtitle="Model the impact of threshold changes on fraud detection, false positives, and review costs"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
        {/* Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Threshold Configuration</h3>

            {currentThresholds && (
              <div style={{ marginBottom: 14, padding: '8px 12px', background: '#0f172a', borderRadius: 8, fontSize: 12, color: '#64748b' }}>
                Current system defaults: low={currentThresholds.low_threshold}, high={currentThresholds.high_threshold}
              </div>
            )}

            {[
              { key: 'low_threshold', label: 'Low → Medium Threshold', min: 1, max: 99, step: 1 },
              { key: 'high_threshold', label: 'Medium → High Threshold', min: 2, max: 100, step: 1 },
            ].map(({ key, label, min, max, step }) => (
              <div key={key} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <label style={{ color: '#94a3b8', fontSize: 12 }}>{label}</label>
                  <span style={{ color: '#6366f1', fontWeight: 700, fontSize: 14 }}>
                    {config[key as keyof SimulatorInput]}
                  </span>
                </div>
                <input
                  type="range" min={min} max={max} step={step}
                  value={config[key as keyof SimulatorInput] as number}
                  onChange={(e) => setConfig({ ...config, [key]: parseFloat(e.target.value) })}
                  style={{ width: '100%', accentColor: '#6366f1' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569', fontSize: 10 }}>
                  <span>{min}</span><span>{max}</span>
                </div>
              </div>
            ))}
          </Card>

          <Card>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Cost Parameters (₹)</h3>
            {[
              { key: 'review_cost_per_case', label: 'Review Cost per Case' },
              { key: 'fraud_loss_per_case', label: 'Fraud Loss per Missed Case' },
            ].map(({ key, label }) => (
              <div key={key} style={{ marginBottom: 12 }}>
                <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>{label}</label>
                <input
                  type="number" min={0} step={100}
                  value={config[key as keyof SimulatorInput] as number}
                  onChange={(e) => setConfig({ ...config, [key]: parseFloat(e.target.value) })}
                  style={inputStyle}
                />
              </div>
            ))}
          </Card>

          <Button onClick={handleSimulate} loading={loading} style={{ justifyContent: 'center' }}>
            ▶ Run Simulation
          </Button>

          <div style={{ padding: '10px 12px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 8, fontSize: 11, color: '#92400e' }}>
            ⚠️ Requires transactions with ground-truth labels. Upload a CSV with an <code>is_fraud_actual</code> column to enable simulation.
          </div>
        </div>

        {/* Results */}
        <div>
          {error && <div style={{ marginBottom: 16 }}><ErrorDisplay message={error} /></div>}

          {!result && !loading && (
            <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
              <div style={{ textAlign: 'center', color: '#64748b' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>⚙️</div>
                <div>Configure thresholds and run simulation</div>
                <div style={{ fontSize: 12, marginTop: 6 }}>Results will compare your config against the baseline</div>
              </div>
            </Card>
          )}

          {loading && <Loading text="Running simulation..." />}

          {result && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Summary metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                <MetricDiff
                  label="Fraud Detected"
                  current={result.detected_fraud}
                  baseline={result.comparison_baseline?.detected_fraud ?? result.detected_fraud}
                  higherIsBetter={true}
                />
                <MetricDiff
                  label="Missed Fraud"
                  current={result.missed_fraud}
                  baseline={result.comparison_baseline?.missed_fraud ?? result.missed_fraud}
                  higherIsBetter={false}
                />
                <MetricDiff
                  label="False Positives"
                  current={result.false_positives}
                  baseline={result.comparison_baseline?.false_positives ?? result.false_positives}
                  higherIsBetter={false}
                />
                <MetricDiff
                  label="Precision"
                  current={result.precision}
                  baseline={result.comparison_baseline?.precision ?? result.precision}
                  format="pct"
                />
                <MetricDiff
                  label="Recall"
                  current={result.recall}
                  baseline={result.comparison_baseline?.recall ?? result.recall}
                  format="pct"
                />
                <MetricDiff
                  label="F1 Score"
                  current={result.f1_score}
                  baseline={result.comparison_baseline?.f1_score ?? result.f1_score}
                  format="pct"
                />
              </div>

              {/* Cost breakdown */}
              <Card>
                <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>Cost Analysis</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                  <div style={{ background: '#0f172a', borderRadius: 8, padding: '12px 14px', border: '1px solid rgba(99,102,241,0.3)' }}>
                    <div style={{ color: '#64748b', fontSize: 12 }}>Review Cost</div>
                    <div style={{ color: '#6366f1', fontSize: 18, fontWeight: 700 }}>₹{result.estimated_review_cost.toLocaleString('en-IN')}</div>
                    <div style={{ color: '#475569', fontSize: 11 }}>{result.false_positives + result.detected_fraud} cases × ₹{config.review_cost_per_case}</div>
                  </div>
                  <div style={{ background: '#0f172a', borderRadius: 8, padding: '12px 14px', border: '1px solid rgba(239,68,68,0.3)' }}>
                    <div style={{ color: '#64748b', fontSize: 12 }}>Fraud Loss</div>
                    <div style={{ color: '#ef4444', fontSize: 18, fontWeight: 700 }}>₹{result.estimated_fraud_loss.toLocaleString('en-IN')}</div>
                    <div style={{ color: '#475569', fontSize: 11 }}>{result.missed_fraud} missed × ₹{config.fraud_loss_per_case}</div>
                  </div>
                  <div style={{ background: '#0f172a', borderRadius: 8, padding: '12px 14px', border: '1px solid rgba(245,158,11,0.3)' }}>
                    <div style={{ color: '#64748b', fontSize: 12 }}>Total Cost</div>
                    <div style={{ color: '#f59e0b', fontSize: 18, fontWeight: 700 }}>₹{result.total_cost.toLocaleString('en-IN')}</div>
                    <div style={{ color: '#475569', fontSize: 11 }}>Review + Losses</div>
                  </div>
                </div>
              </Card>

              {/* Chart: Your config vs baseline */}
              {result.comparison_baseline && (
                <Card>
                  <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>Your Config vs Baseline</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={[
                      {
                        name: 'Detected Fraud',
                        yours: result.detected_fraud,
                        baseline: result.comparison_baseline.detected_fraud,
                      },
                      {
                        name: 'False Positives',
                        yours: result.false_positives,
                        baseline: result.comparison_baseline.false_positives,
                      },
                      {
                        name: 'Missed Fraud',
                        yours: result.missed_fraud,
                        baseline: result.comparison_baseline.missed_fraud,
                      },
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                      <Legend />
                      <Bar dataKey="yours" fill="#6366f1" name="Your Config" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="baseline" fill="#475569" name="Baseline" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              )}

              {/* Radar chart for model quality */}
              <Card>
                <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>Detection Quality Radar</h4>
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={[
                    { metric: 'Precision', value: result.precision * 100 },
                    { metric: 'Recall', value: result.recall * 100 },
                    { metric: 'F1 Score', value: result.f1_score * 100 },
                    {
                      metric: 'Coverage',
                      value: result.total_transactions > 0
                        ? (result.detected_fraud / (result.detected_fraud + result.missed_fraud || 1)) * 100
                        : 0,
                    },
                    {
                      metric: 'Specificity',
                      value: result.total_transactions > 0
                        ? (result.true_negatives / (result.true_negatives + result.false_positives || 1)) * 100
                        : 0,
                    },
                  ]}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
                    <Radar name="Metrics" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
