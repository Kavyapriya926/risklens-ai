import React from 'react';
import { Sidebar } from './Sidebar';

interface Props { children: React.ReactNode }

export const Layout: React.FC<Props> = ({ children }) => (
  <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a', color: '#f1f5f9' }}>
    <Sidebar />
    <main style={{ flex: 1, padding: '28px 32px', overflow: 'auto', minWidth: 0 }}>
      {children}
    </main>
  </div>
);
