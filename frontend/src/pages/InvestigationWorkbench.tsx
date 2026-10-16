import React, { useState } from 'react';
import { listInvestigations, reviewInvestigation, addInvestigationNote, getAuditHistory } from '../api/client';
import type { Investigation, AuditLog } from '../types';
import { Card, Badge, Button, Loading, ErrorDisplay, PageHeader } from '../components/common/Card';
import { RiskScore } from '../components/common/RiskScore';
import { useApi } from '../hooks/useApi';
import type { RiskLevel } from '../types';

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#22c55e',
};

export const InvestigationWorkbench: React.FC = () => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [selected, setSelected] = useState<Investigation | null>(null);
  const [auditLog, setAuditLog] = useState<AuditLog[]>([]);
  const [noteText, setNoteText] = useState('');
  const [analystId, setAnalystId] = useState('analyst_01');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'notes' | 'audit'>('details');

  const params = {
    limit: 100,
    ...(statusFilter ? { status: statusFilter } : {}),
    ...(priorityFilter ? { priority: priorityFilter } : {}),
    ...(search ? { search } : {}),
  };
  const { data: investigations, loading, error, refetch } = useApi(
    () => listInvestigations(params),
    [search, statusFilter, priorityFilter]
  );

  const loadAudit = async (id: string) => {
    try {
      const logs = await getAuditHistory(id);
      setAuditLog(logs);
    } catch { setAuditLog([]); }
  };

  const selectInvestigation = (inv: Investigation) => {
    setSelected(inv);
    setActiveTab('details');
    loadAudit(inv.id);
  };

  const handleAction = async (action: string, verdict?: string) => {
    if (!selected) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const updated = await reviewInvestigation(selected.id, {
        analyst_id: analystId,
        action,
        ...(verdict ? { verdict } : {}),
      });
      setSelected(updated);
      loadAudit(selected.id);
      refetch();
    } catch (e: unknown) {
      setActionError((e as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddNote = async () => {
    if (!selected || !noteText.trim()) return;
    setActionLoading(true);
    try {
      await addInvestigationNote(selected.id, {
        analyst_id: analystId,
        content: noteText.trim(),
        note_type: 'general',
      });
      setNoteText('');
      const fresh = (await listInvestigations({ limit: 100 })).find(i => i.id === selected.id);
      if (fresh) setSelected(fresh);
      loadAudit(selected.id);
    } catch (e: unknown) {
      setActionError((e as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
    padding: '8px 12px', color: '#f1f5f9', fontSize: 13, outline: 'none', width: '100%', boxSizing: 'border-box',
  };

  const statusAllowed: Record<string, string[]> = {
    open: ['review', 'escalate', 'close'],
    reviewed: ['escalate', 'reopen', 'close'],
    escalated: ['review', 'close'],
    closed: ['reopen'],
  };

  return (
    <div>
      <PageHeader
        title="Investigation Workbench"
        subtitle="Review, escalate, and resolve flagged transactions"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 20, minHeight: 600 }}>
        {/* Queue */}
        <div>
          <Card style={{ padding: 12, marginBottom: 12 }}>
            <input
              placeholder="Search by transaction ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ ...inputStyle, marginBottom: 8 }}
            />
            <div style={{ display: 'flex', gap: 6 }}>
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
                <option value="">All Status</option>
                {['open', 'reviewed', 'escalated', 'closed'].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
                <option value="">All Priority</option>
                {['critical', 'high', 'medium', 'low'].map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </Card>

          {loading ? (
            <Loading text="Loading queue..." />
          ) : error ? (
            <ErrorDisplay message={error} onRetry={refetch} />
          ) : (
            <div style={{ maxHeight: 600, overflowY: 'auto' }}>
              {(investigations || []).length === 0 && (
                <div style={{ textAlign: 'center', padding: 32, color: '#64748b', fontSize: 13 }}>
                  No investigations found.<br />Analyze some transactions first.
                </div>
              )}
              {(investigations || []).map((inv) => (
                <div
                  key={inv.id}
                  onClick={() => selectInvestigation(inv)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 8,
                    marginBottom: 6,
                    cursor: 'pointer',
                    background: selected?.id === inv.id ? 'rgba(99,102,241,0.12)' : '#1e293b',
                    border: selected?.id === inv.id ? '1px solid #6366f1' : '1px solid #334155',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <code style={{ color: '#f1f5f9', fontSize: 12 }}>{inv.transaction_id}</code>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: inv.status === 'open' ? '#ef4444' : inv.status === 'escalated' ? '#f97316' : '#22c55e',
                      display: 'inline-block',
                    }} />
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 11, color: PRIORITY_COLORS[inv.priority] || '#94a3b8', fontWeight: 600 }}>
                      {inv.priority.toUpperCase()}
                    </span>
                    <span style={{ color: '#64748b', fontSize: 11 }}>{inv.status}</span>
                    {inv.risk_score !== undefined && (
                      <span style={{ color: '#94a3b8', fontSize: 11 }}>Score: {inv.risk_score.toFixed(0)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <div>
          {!selected ? (
            <Card style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
              <div style={{ textAlign: 'center', color: '#64748b' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🕵️</div>
                <div>Select an investigation from the queue</div>
              </div>
            </Card>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Header */}
              <Card>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                      <code style={{ color: '#f1f5f9', fontSize: 15, fontWeight: 600 }}>{selected.transaction_id}</code>
                      <Badge label={selected.status} variant={
                        selected.status === 'open' ? 'high' :
                          selected.status === 'escalated' ? 'warning' :
                            selected.status === 'closed' ? 'low' : 'info'
                      } />
                      <Badge label={selected.priority} variant={
                        selected.priority === 'critical' ? 'high' :
                          selected.priority === 'high' ? 'high' :
                            selected.priority === 'medium' ? 'warning' : 'low'
                      } />
                    </div>
                    <div style={{ color: '#64748b', fontSize: 12 }}>
                      Created: {new Date(selected.created_at).toLocaleString()} ·
                      Updated: {new Date(selected.updated_at).toLocaleString()}
                    </div>
                    {selected.analyst_verdict && (
                      <div style={{ marginTop: 4, color: '#94a3b8', fontSize: 13 }}>
                        Verdict: <strong style={{ color: selected.analyst_verdict === 'fraud' ? '#ef4444' : '#22c55e' }}>
                          {selected.analyst_verdict}
                        </strong>
                      </div>
                    )}
                  </div>
                  {selected.risk_score !== undefined && selected.risk_level && (
                    <RiskScore score={selected.risk_score} level={selected.risk_level as RiskLevel} size="md" />
                  )}
                </div>
              </Card>

              {/* Analyst ID */}
              <Card style={{ padding: '12px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <label style={{ color: '#64748b', fontSize: 13, whiteSpace: 'nowrap' }}>Your Analyst ID:</label>
                  <input value={analystId} onChange={(e) => setAnalystId(e.target.value)}
                    style={{ ...inputStyle, maxWidth: 200 }} />
                </div>
              </Card>

              {actionError && <ErrorDisplay message={actionError} onRetry={() => setActionError(null)} />}

              {/* Actions */}
              <Card>
                <h4 style={{ margin: '0 0 12px', color: '#f1f5f9', fontSize: 14 }}>Actions</h4>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {(statusAllowed[selected.status] || []).includes('review') && (
                    <>
                      <Button size="sm" onClick={() => handleAction('review', 'legitimate')} loading={actionLoading} variant="secondary">
                        ✅ Mark Legitimate
                      </Button>
                      <Button size="sm" onClick={() => handleAction('review', 'fraud')} loading={actionLoading} variant="danger">
                        🚨 Confirm Fraud
                      </Button>
                    </>
                  )}
                  {(statusAllowed[selected.status] || []).includes('escalate') && (
                    <Button size="sm" onClick={() => handleAction('escalate')} loading={actionLoading} variant="secondary" style={{ borderColor: '#f97316', color: '#f97316' }}>
                      ⬆️ Escalate
                    </Button>
                  )}
                  {(statusAllowed[selected.status] || []).includes('close') && (
                    <Button size="sm" onClick={() => handleAction('close')} loading={actionLoading} variant="ghost">
                      🔒 Close
                    </Button>
                  )}
                  {(statusAllowed[selected.status] || []).includes('reopen') && (
                    <Button size="sm" onClick={() => handleAction('reopen')} loading={actionLoading} variant="secondary">
                      🔓 Reopen
                    </Button>
                  )}
                </div>
              </Card>

              {/* Tabs */}
              <Card>
                <div style={{ display: 'flex', gap: 2, marginBottom: 16, background: '#0f172a', padding: 3, borderRadius: 8, width: 'fit-content' }}>
                  {(['details', 'notes', 'audit'] as const).map((t) => (
                    <button key={t} onClick={() => setActiveTab(t)} style={{
                      padding: '6px 14px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12,
                      background: activeTab === t ? '#6366f1' : 'transparent',
                      color: activeTab === t ? '#fff' : '#64748b',
                    }}>
                      {t.charAt(0).toUpperCase() + t.slice(1)} {t === 'notes' ? `(${selected.notes.length})` : t === 'audit' ? `(${auditLog.length})` : ''}
                    </button>
                  ))}
                </div>

                {activeTab === 'details' && (
                  <div style={{ color: '#94a3b8', fontSize: 13, lineHeight: 2 }}>
                    <div><strong>Status:</strong> {selected.status}</div>
                    <div><strong>Priority:</strong> {selected.priority}</div>
                    <div><strong>Risk Level:</strong> {selected.risk_level}</div>
                    <div><strong>Risk Score:</strong> {selected.risk_score?.toFixed(1)}</div>
                    {selected.analyst_id && <div><strong>Reviewed by:</strong> {selected.analyst_id}</div>}
                    {selected.reviewed_at && <div><strong>Reviewed at:</strong> {new Date(selected.reviewed_at).toLocaleString()}</div>}
                  </div>
                )}

                {activeTab === 'notes' && (
                  <div>
                    {selected.notes.map((note) => (
                      <div key={note.id} style={{ marginBottom: 10, padding: '10px 12px', background: '#0f172a', borderRadius: 8, borderLeft: '3px solid #6366f1' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span style={{ color: '#6366f1', fontSize: 12, fontWeight: 600 }}>{note.analyst_id}</span>
                          <span style={{ color: '#64748b', fontSize: 11 }}>{new Date(note.created_at).toLocaleString()}</span>
                        </div>
                        <div style={{ color: '#94a3b8', fontSize: 13 }}>{note.content}</div>
                      </div>
                    ))}
                    <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                      <textarea
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        placeholder="Add an analyst note..."
                        rows={2}
                        style={{ ...inputStyle, flex: 1, resize: 'vertical', fontFamily: 'inherit' }}
                      />
                      <Button size="sm" onClick={handleAddNote} loading={actionLoading} style={{ alignSelf: 'flex-end' }}>
                        Add
                      </Button>
                    </div>
                  </div>
                )}

                {activeTab === 'audit' && (
                  <div>
                    {auditLog.length === 0 ? (
                      <div style={{ color: '#64748b', fontSize: 13 }}>No audit entries yet.</div>
                    ) : auditLog.map((log) => (
                      <div key={log.id} style={{ marginBottom: 8, padding: '8px 12px', background: '#0f172a', borderRadius: 6 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                          <span style={{ color: '#f59e0b', fontSize: 12, fontWeight: 600 }}>{log.action}</span>
                          <span style={{ color: '#64748b', fontSize: 11 }}>{new Date(log.created_at).toLocaleString()}</span>
                        </div>
                        <div style={{ color: '#94a3b8', fontSize: 12 }}>{log.description}</div>
                        <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>by {log.actor_id}</div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
