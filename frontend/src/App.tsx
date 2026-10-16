import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { TransactionAnalysis } from './pages/TransactionAnalysis';
import { InvestigationWorkbench } from './pages/InvestigationWorkbench';
import { RiskSimulator } from './pages/RiskSimulator';
import { ModelEvaluation } from './pages/ModelEvaluation';

const App: React.FC = () => (
  <BrowserRouter>
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analyze" element={<TransactionAnalysis />} />
        <Route path="/investigations" element={<InvestigationWorkbench />} />
        <Route path="/simulator" element={<RiskSimulator />} />
        <Route path="/evaluation" element={<ModelEvaluation />} />
        <Route path="*" element={
          <div style={{ textAlign: 'center', padding: 80, color: '#64748b' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>404</div>
            <div>Page not found</div>
          </div>
        } />
      </Routes>
    </Layout>
  </BrowserRouter>
);

export default App;
