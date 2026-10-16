import React, { useState, useRef } from 'react';
import { analyzeTransaction, uploadCSV } from '../api/client';
import type { TransactionInput, TransactionResult, BatchUploadResult } from '../types';
import { Card, Button, PageHeader, ErrorDisplay, Badge, Loading } from '../components/common/Card';
import { RiskScore } from '../components/common/RiskScore';
import type { RiskLevel } from '../types';

const CATEGORIES = [
  'retail', 'food_beverage', 'travel', 'electronics', 'utilities',
  'entertainment', 'healthcare', 'education', 'financial_services',
  'online_marketplace', 'fuel', 'grocery', 'jewelry', 'gaming', 'other',
];

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const defaultForm: TransactionInput = {
  amount: 5000,
  merchant_category: 'retail',
  hour_of_day: 10,
  day_of_week: 1,
  is_international: false,
  is_new_merchant: false,
  velocity_24h: 1,
  card_age_days: 365,
  distance_from_home_km: 5,
};

export const TransactionAnalysis: React.FC = () => {
  const [form, setForm] = useState<TransactionInput>(defaultForm);
  const [result, setResult] = useState<TransactionResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchUploadResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'manual' | 'csv'>('manual');
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await analyzeTransaction(form);
      setResult(r);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    setBatchResult(null);
    try {
      const r = await uploadCSV(file);
      setBatchResult(r);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500 }}>{label}</label>
      {children}
    </div>
  );

  const inputStyle: React.CSSProperties = {
    background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
    padding: '8px 12px', color: '#f1f5f9', fontSize: 14, outline: 'none',
  };

  return (
    <div>
      <PageHeader title="Transaction Analysis" subtitle="Analyze individual transactions or upload a CSV batch" />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 20, background: '#1e293b', padding: 4, borderRadius: 10, width: 'fit-content', border: '1px solid #334155' }}>
        {(['manual', 'csv'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '8px 20px', borderRadius: 7, border: 'none',
            cursor: 'pointer', fontSize: 13, fontWeight: 500,
            background: tab === t ? '#6366f1' : 'transparent',
            color: tab === t ? '#fff' : '#64748b',
            transition: 'all 0.15s',
          }}>
            {t === 'manual' ? '✍️ Manual Input' : '📁 CSV Upload'}
          </button>
        ))}
      </div>

      {error && <div style={{ marginBottom: 16 }}><ErrorDisplay message={error} onRetry={() => setError(null)} /></div>}

      <div style={{ display: 'grid', gridTemplateColumns: result || batchResult ? '1fr 1fr' : '1fr', gap: 20 }}>
        {/* Input Form */}
        <div>
          {tab === 'manual' ? (
            <Card>
              <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontSize: 15 }}>Transaction Details</h3>
              <form onSubmit={handleSubmit}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <Field label="Amount (₹)">
                    <input type="number" min={1} max={10000000} required value={form.amount}
                      onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) })}
                      style={inputStyle} />
                  </Field>

                  <Field label="Merchant Category">
                    <select value={form.merchant_category}
                      onChange={(e) => setForm({ ...form, merchant_category: e.target.value })}
                      style={inputStyle}>
                      {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
                    </select>
                  </Field>

                  <Field label="Hour of Day (0–23)">
                    <input type="number" min={0} max={23} value={form.hour_of_day}
                      onChange={(e) => setForm({ ...form, hour_of_day: parseInt(e.target.value) })}
                      style={inputStyle} />
                  </Field>

                  <Field label="Day of Week">
                    <select value={form.day_of_week}
                      onChange={(e) => setForm({ ...form, day_of_week: parseInt(e.target.value) })}
                      style={inputStyle}>
                      {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                    </select>
                  </Field>

                  <Field label="Transactions (last 24h)">
                    <input type="number" min={1} max={1000} value={form.velocity_24h}
                      onChange={(e) => setForm({ ...form, velocity_24h: parseInt(e.target.value) })}
                      style={inputStyle} />
                  </Field>

                  <Field label="Card Age (days)">
                    <input type="number" min={0} value={form.card_age_days ?? ''}
                      onChange={(e) => setForm({ ...form, card_age_days: parseInt(e.target.value) || undefined })}
                      style={inputStyle} />
                  </Field>

                  <Field label="Distance from Home (km)">
                    <input type="number" min={0} value={form.distance_from_home_km ?? ''}
                      onChange={(e) => setForm({ ...form, distance_from_home_km: parseFloat(e.target.value) || undefined })}
                      style={inputStyle} />
                  </Field>

                  <Field label="Merchant ID (optional)">
                    <input type="text" maxLength={64} value={form.merchant_id ?? ''}
                      onChange={(e) => setForm({ ...form, merchant_id: e.target.value || undefined })}
                      style={inputStyle} />
                  </Field>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', color: '#94a3b8', fontSize: 13 }}>
                      <input type="checkbox" checked={form.is_international}
                        onChange={(e) => setForm({ ...form, is_international: e.target.checked })} />
                      International Transaction
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', color: '#94a3b8', fontSize: 13 }}>
                      <input type="checkbox" checked={form.is_new_merchant}
                        onChange={(e) => setForm({ ...form, is_new_merchant: e.target.checked })} />
                      New Merchant
                    </label>
                  </div>
                </div>

                <Button
                  type="submit"
                  loading={loading}
                  style={{ marginTop: 20, width: '100%', justifyContent: 'center' }}
                >
                  🔍 Analyze Transaction
                </Button>
              </form>
            </Card>
          ) : (
            <Card>
              <h3 style={{ margin: '0 0 12px', color: '#f1f5f9', fontSize: 15 }}>CSV Batch Upload</h3>
              <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 16px' }}>
                Upload a CSV with columns: <code style={{ color: '#94a3b8' }}>amount, merchant_category, hour_of_day, day_of_week, is_international, is_new_merchant, card_age_days, velocity_24h, distance_from_home_km</code>
              </p>
              <div style={{
                border: '2px dashed #334155', borderRadius: 10, padding: 32,
                textAlign: 'center', cursor: 'pointer',
                background: '#0f172a',
              }}
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files?.[0];
                  if (f) {
                    const dt = new DataTransfer();
                    dt.items.add(f);
                    if (fileRef.current) {
                      fileRef.current.files = dt.files;
                      handleFileUpload({ target: { files: dt.files } } as any);
                    }
                  }
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>📁</div>
                <div style={{ color: '#94a3b8', fontSize: 14 }}>Drop CSV here or click to browse</div>
                <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>Max 10 MB · 10,000 rows · UTF-8</div>
                <input ref={fileRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={handleFileUpload} />
              </div>
              {loading && <Loading text="Processing CSV..." />}

              <div style={{ marginTop: 16, padding: '12px', background: '#0f172a', borderRadius: 8 }}>
                <div style={{ color: '#6366f1', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>📥 Sample CSV format:</div>
                <code style={{ color: '#64748b', fontSize: 11, display: 'block', lineHeight: 1.6 }}>
                  transaction_id,amount,merchant_category,hour_of_day,day_of_week,is_international,is_new_merchant,card_age_days,velocity_24h,distance_from_home_km<br />
                  TXN001,5000,retail,10,2,false,false,365,1,5.0<br />
                  TXN002,95000,jewelry,2,6,true,true,5,15,900.0
                </code>
              </div>
            </Card>
          )}
        </div>

        {/* Results */}
        {result && tab === 'manual' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Score Card */}
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                <RiskScore score={result.risk_score} level={result.risk_level} size="lg" />
                <div>
                  <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
                    Risk Analysis Complete
                  </div>
                  <div style={{ color: '#64748b', fontSize: 13 }}>Txn: {result.transaction_id}</div>
                  <div style={{ color: '#64748b', fontSize: 13 }}>Model: {result.model_version}</div>
                  <div style={{ color: '#64748b', fontSize: 13 }}>
                    Confidence: {(result.prediction_confidence * 100).toFixed(1)}% · {result.processing_time_ms.toFixed(0)}ms
                  </div>
                </div>
              </div>
            </Card>

            {/* Evidence Summary */}
            <Card>
              <h4 style={{ margin: '0 0 10px', color: '#f1f5f9', fontSize: 14 }}>Evidence Summary</h4>
              <div style={{
                background: '#0f172a', borderRadius: 8, padding: '12px 14px',
                color: '#94a3b8', fontSize: 13, lineHeight: 1.6,
                border: '1px solid #334155',
              }}>
                {result.explanation.evidence_summary}
              </div>
            </Card>

            {/* Feature Contributions */}
            <Card>
              <h4 style={{ margin: '0 0 12px', color: '#f1f5f9', fontSize: 14 }}>Feature Contributions</h4>
              {result.explanation.factors.slice(0, 8).map((f) => (
                <div key={f.feature} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12 }}>{f.human_label}</span>
                    <span style={{
                      fontSize: 11, fontWeight: 600,
                      color: f.direction === 'increases_risk' ? '#ef4444' : '#22c55e',
                    }}>
                      {f.direction === 'increases_risk' ? '▲' : '▼'} {Math.abs(f.contribution).toFixed(3)}
                    </span>
                  </div>
                  <div style={{ height: 4, borderRadius: 2, background: '#334155' }}>
                    <div style={{
                      height: '100%', borderRadius: 2,
                      width: `${Math.min(Math.abs(f.contribution) / 0.5 * 100, 100)}%`,
                      background: f.direction === 'increases_risk' ? '#ef4444' : '#22c55e',
                      transition: 'width 0.4s',
                    }} />
                  </div>
                </div>
              ))}
            </Card>
          </div>
        )}

        {/* Batch Result */}
        {batchResult && tab === 'csv' && (
          <Card>
            <h3 style={{ margin: '0 0 16px', color: '#f1f5f9', fontSize: 15 }}>Batch Upload Results</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Total Rows', value: batchResult.total_rows, color: '#6366f1' },
                { label: 'Processed', value: batchResult.processed, color: '#22c55e' },
                { label: 'High Risk', value: batchResult.high_risk_count, color: '#ef4444' },
                { label: 'Medium Risk', value: batchResult.medium_risk_count, color: '#f59e0b' },
                { label: 'Low Risk', value: batchResult.low_risk_count, color: '#22c55e' },
                { label: 'Failed', value: batchResult.failed, color: '#ef4444' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: '#0f172a', borderRadius: 8, padding: '12px 14px' }}>
                  <div style={{ color: '#64748b', fontSize: 12 }}>{label}</div>
                  <div style={{ color, fontSize: 22, fontWeight: 700 }}>{value}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, padding: '8px 12px', background: '#0f172a', borderRadius: 8, fontSize: 12, color: '#64748b' }}>
              Batch ID: {batchResult.batch_id}
            </div>
            {batchResult.errors.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ color: '#ef4444', fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Errors:</div>
                {batchResult.errors.slice(0, 5).map((e, i) => (
                  <div key={i} style={{ color: '#94a3b8', fontSize: 12, padding: '4px 0' }}>• {e}</div>
                ))}
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};
