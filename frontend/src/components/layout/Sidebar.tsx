import React from 'react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/analyze', label: 'Transaction Analysis', icon: '🔍' },
  { path: '/investigations', label: 'Investigations', icon: '🕵️' },
  { path: '/simulator', label: 'Risk Simulator', icon: '⚙️' },
  { path: '/evaluation', label: 'Model Evaluation', icon: '📈' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside style={{
      width: 240,
      minHeight: '100vh',
      background: '#1e293b',
      borderRight: '1px solid #334155',
      display: 'flex',
      flexDirection: 'column',
      padding: '0',
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid #334155' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18,
          }}>🛡️</div>
          <div>
            <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 15, lineHeight: 1.2 }}>RiskLens AI</div>
            <div style={{ color: '#64748b', fontSize: 11 }}>Fraud Risk Manager</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: '12px 8px', flex: 1 }}>
        {navItems.map(({ path, label, icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 12px',
              borderRadius: 8,
              marginBottom: 2,
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: isActive ? 600 : 400,
              color: isActive ? '#f1f5f9' : '#94a3b8',
              background: isActive ? 'rgba(99,102,241,0.15)' : 'transparent',
              borderLeft: isActive ? '2px solid #6366f1' : '2px solid transparent',
              transition: 'all 0.15s',
            })}
          >
            <span style={{ fontSize: 16 }}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Demo badge */}
      <div style={{
        margin: 12,
        padding: '8px 12px',
        background: 'rgba(245,158,11,0.1)',
        borderRadius: 8,
        border: '1px solid rgba(245,158,11,0.3)',
      }}>
        <div style={{ color: '#fbbf24', fontSize: 11, fontWeight: 600 }}>⚠️ DEMO SYSTEM</div>
        <div style={{ color: '#92400e', fontSize: 10, marginTop: 2 }}>Not for real financial decisions</div>
      </div>
    </aside>
  );
};
