import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar, Legend,
} from 'recharts';
import { getModelEvaluation, getModelMonitoring, triggerTraining } from '../api/client';
import { Card, Loading, ErrorDisplay, PageHeader, Button, Badge } from '../components/common/Card';
import { useApi } from '../hooks/useApi';

export const ModelEvaluation: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState<'best' | 'logistic_regression' | 'random_forest'>('best');
  const [trainingMsg, setTrainingMsg] = useState<string | null>(null);
  const [trainingLoading, setTrainingLoading] = useState(false);

  const evalApi = useApi(() => getModelEvaluation(selectedModel), [selectedModel]);
  const monitorApi = useApi(getModelMonitoring, []);

  const handleRetrain = async () => {
    setTrainingLoading(true);
    setTrainingMsg(null);
    try {
      const r = await triggerTraining();
      setTrainingMsg(r.message);
      setTimeout(() => {
        evalApi.refetch();
        monitorApi.refetch();
      }, 3000);
    } catch (e: unknown) {
      setTrainingMsg(`Error: ${(e as Error).message}`);
    } finally {
      setTrainingLoading(false);
    }
  };

  const MetricBox: React.FC<{ label: string; value: string | number; color?: string; description?: string }> = ({
    label, value, color = '#6366f1', description,
  }) => (
    <div style={{ background: '#0f172a', borderRadius: 10, padding: '14px 16px', border: `1px solid ${color}33` }}>
      <div style={{ color: '#64748b', fontSize: 12, marginBottom: 4 }}>{label}</div>
      <div style={{ color, fontSize: 26, fontWeight: 700 }}>{value}</div>
      {description && <div style={{ color: '#475569', fontSize: 11, marginTop: 2 }}>{description}</div>}
    </div>
  );

  return (
    <div>
      <PageHeader
        title="Model Evaluation"
        subtitle="Metrics computed on a genuinely held-out 20% test set"
        action={
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as typeof selectedModel)}
              style={{
                background: '#1e293b', border: '1px solid #334155', borderRadius: 8,
                padding: '8px 12px', color: '#f1f5f9', fontSize: 13, outline: 'none',
              }}
            >
              <option value="best">Best Model</option>
              <option value="logistic_regression">Logistic Regression</option>
              <option value="random_forest">Random Forest</option>
            </select>
            <Button variant="secondary" size="sm" onClick={handleRetrain} loading={trainingLoading}>
              🔄 Retrain
            </Button>
          </div>
        }
      />

      {trainingMsg && (
        <div style={{
          marginBottom: 16, padding: '10px 14px',
          background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)',
          borderRadius: 8, color: '#a5b4fc', fontSize: 13,
        }}>
          {trainingMsg}
        </div>
      )}

      {/* Evaluation Report */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div>
          {evalApi.loading ? (
            <Loading text="Loading evaluation..." />
          ) : evalApi.error ? (
            <ErrorDisplay message={evalApi.error} onRetry={evalApi.refetch} />
          ) : evalApi.data ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Model Info */}
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                  <div>
                    <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 16 }}>
                      {evalApi.data.model_name.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </div>
                    <div style={{ color: '#64748b', fontSize: 12, marginTop: 3 }}>
                      Version: {evalApi.data.model_version} · Trained: {new Date(evalApi.data.trained_at).toLocaleString()}
                    </div>
                  </div>
                  <Badge label="SYNTHETIC DATA" variant="warning" />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 14 }}>
                  <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', fontSize: 12 }}>
                    <div style={{ color: '#64748b' }}>Dataset</div>
                    <div style={{ color: '#f1f5f9', fontWeight: 600 }}>{evalApi.data.dataset_size.toLocaleString()}</div>
                  </div>
                  <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', fontSize: 12 }}>
                    <div style={{ color: '#64748b' }}>Train / Test</div>
                    <div style={{ color: '#f1f5f9', fontWeight: 600 }}>{evalApi.data.train_size} / {evalApi.data.test_size}</div>
                  </div>
                  <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', fontSize: 12 }}>
                    <div style={{ color: '#64748b' }}>Fraud Rate</div>
                    <div style={{ color: '#f59e0b', fontWeight: 600 }}>{evalApi.data.fraud_rate_pct}%</div>
                  </div>
                </div>
              </Card>

              {/* Core Metrics */}
              <Card>
                <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>
                  Test Set Metrics <span style={{ color: '#64748b', fontWeight: 400, fontSize: 12 }}>(held-out 20%)</span>
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <MetricBox label="Precision" value={evalApi.data.metrics.precision.toFixed(4)} color="#6366f1"
                    description="True positives / (True + False positives)" />
                  <MetricBox label="Recall" value={evalApi.data.metrics.recall.toFixed(4)} color="#22c55e"
                    description="True positives / (True positives + False negatives)" />
                  <MetricBox label="F1 Score" value={evalApi.data.metrics.f1_score.toFixed(4)} color="#8b5cf6"
                    description="Harmonic mean of precision and recall" />
                  <MetricBox label="PR-AUC" value={evalApi.data.metrics.pr_auc.toFixed(4)} color="#06b6d4"
                    description="Area under Precision-Recall curve" />
                  <MetricBox label="False Positive Rate" value={evalApi.data.metrics.false_positive_rate.toFixed(4)} color="#ef4444"
                    description="False positives / (FP + True negatives)" />
                  <MetricBox label="Threshold" value={evalApi.data.threshold_used.toFixed(2)} color="#f59e0b"
                    description="Decision threshold used for binary prediction" />
                </div>
              </Card>

              {/* Confusion Matrix */}
              <Card>
                <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>Confusion Matrix</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, maxWidth: 280 }}>
                  {[
                    { label: 'True Negative', value: evalApi.data.confusion_matrix[0][0], color: '#22c55e' },
                    { label: 'False Positive', value: evalApi.data.confusion_matrix[0][1], color: '#ef4444' },
                    { label: 'False Negative', value: evalApi.data.confusion_matrix[1][0], color: '#f59e0b' },
                    { label: 'True Positive', value: evalApi.data.confusion_matrix[1][1], color: '#6366f1' },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{
                      background: `${color}15`, border: `1px solid ${color}40`,
                      borderRadius: 8, padding: '12px 14px', textAlign: 'center',
                    }}>
                      <div style={{ color, fontSize: 22, fontWeight: 700 }}>{value.toLocaleString()}</div>
                      <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>{label}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 10, fontSize: 11, color: '#475569' }}>
                  Rows = Actual · Columns = Predicted · Threshold = {evalApi.data.threshold_used}
                </div>
              </Card>

              {/* Disclaimer */}
              <div style={{
                padding: '10px 14px',
                background: 'rgba(245,158,11,0.08)',
                border: '1px solid rgba(245,158,11,0.25)',
                borderRadius: 8, fontSize: 11, color: '#92400e', lineHeight: 1.5,
              }}>
                ⚠️ {evalApi.data.disclaimer}
              </div>
            </div>
          ) : null}
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* PR Curve */}
          {evalApi.data && (
            <Card>
              <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>Precision-Recall Curve</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={evalApi.data.pr_curve_points}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="recall" type="number" domain={[0, 1]} stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: 'Recall', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 11 }} />
                  <YAxis domain={[0, 1]} stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: 'Precision', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                    formatter={(v: number) => v.toFixed(4)}
                  />
                  <Line type="monotone" dataKey="precision" stroke="#6366f1" dot={false} strokeWidth={2} name="Precision" />
                </LineChart>
              </ResponsiveContainer>
              <div style={{ color: '#64748b', fontSize: 11, marginTop: 6 }}>
                PR-AUC = {evalApi.data.metrics.pr_auc.toFixed(4)} — higher is better for imbalanced datasets
              </div>
            </Card>
          )}

          {/* Feature Importances */}
          {evalApi.data && evalApi.data.feature_importances.length > 0 && (
            <Card>
              <h4 style={{ margin: '0 0 14px', color: '#f1f5f9', fontSize: 14 }}>Feature Importances</h4>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={evalApi.data.feature_importances.slice(0, 10)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                  <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="label" stroke="#64748b" tick={{ fontSize: 10 }} width={130} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                  <Bar dataKey="importance" fill="#6366f1" name="Importance" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      </div>

      {/* Drift Monitor */}
      <Card>
        <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Model Monitoring & Data Drift</h3>
        {monitorApi.loading ? (
          <Loading text="Loading monitoring data..." />
        ) : monitorApi.error ? (
          <ErrorDisplay message={monitorApi.error} onRetry={monitorApi.refetch} />
        ) : monitorApi.data ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
              <div style={{ background: '#0f172a', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ color: '#64748b', fontSize: 12 }}>Model Version</div>
                <div style={{ color: '#f1f5f9', fontWeight: 600, fontSize: 13, marginTop: 2 }}>
                  {monitorApi.data.model_version || '—'}
                </div>
              </div>
              <div style={{ background: '#0f172a', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ color: '#64748b', fontSize: 12 }}>Best Model</div>
                <div style={{ color: '#f1f5f9', fontWeight: 600, fontSize: 13, marginTop: 2 }}>
                  {monitorApi.data.best_model || '—'}
                </div>
              </div>
              <div style={{ background: '#0f172a', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ color: '#64748b', fontSize: 12 }}>Drift Severity</div>
                <div style={{
                  fontWeight: 600, fontSize: 13, marginTop: 2,
                  color: monitorApi.data.drift_report?.drift_severity === 'high' ? '#ef4444' :
                    monitorApi.data.drift_report?.drift_severity === 'medium' ? '#f59e0b' : '#22c55e',
                }}>
                  {monitorApi.data.drift_report?.drift_severity || '—'}
                </div>
              </div>
              <div style={{ background: '#0f172a', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ color: '#64748b', fontSize: 12 }}>Data Source</div>
                <div style={{ color: '#f59e0b', fontWeight: 600, fontSize: 13, marginTop: 2 }}>
                  {monitorApi.data.data_source || '—'}
                </div>
              </div>
            </div>

            {monitorApi.data.drift_report?.recommendation && (
              <div style={{
                padding: '10px 14px', background: '#0f172a', borderRadius: 8,
                border: '1px solid #334155', color: '#94a3b8', fontSize: 13, marginBottom: 16,
              }}>
                💡 {monitorApi.data.drift_report.recommendation}
              </div>
            )}

            {(monitorApi.data.drift_report?.feature_drift || []).length > 0 && (
              <div>
                <div style={{ color: '#64748b', fontSize: 12, marginBottom: 8 }}>Feature Drift (PSI) — Last 30 days vs Training</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
                  {monitorApi.data.drift_report.feature_drift.slice(0, 12).map((f: any) => (
                    <div key={f.feature} style={{
                      background: '#0f172a', borderRadius: 8, padding: '8px 10px',
                      border: `1px solid ${f.severity === 'high' ? '#ef444440' : f.severity === 'medium' ? '#f59e0b40' : '#33415560'}`,
                    }}>
                      <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 3 }}>{f.label}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{
                          fontSize: 13, fontWeight: 600,
                          color: f.severity === 'high' ? '#ef4444' : f.severity === 'medium' ? '#f59e0b' : '#22c55e',
                        }}>
                          PSI {f.psi.toFixed(3)}
                        </span>
                        <span style={{ fontSize: 10, color: '#475569' }}>{f.severity}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </Card>
    </div>
  );
};
