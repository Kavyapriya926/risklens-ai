import axios from 'axios';
import type {
  TransactionInput, TransactionResult, TransactionDetail, BatchUploadResult,
  DashboardStats, DashboardCharts, Investigation, SimulatorInput, SimulatorResult,
  ModelEvaluationReport,
} from '../types';

const BASE_URL = (import.meta as any).env?.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'An unexpected error occurred';
    return Promise.reject(new Error(typeof msg === 'string' ? msg : JSON.stringify(msg)));
  }
);

// Transactions
export const analyzeTransaction = (data: TransactionInput) =>
  api.post<TransactionResult>('/api/transactions/analyze', data).then((r) => r.data);

export const uploadCSV = (file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api
    .post<BatchUploadResult>('/api/transactions/upload-csv', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    .then((r) => r.data);
};

export const listTransactions = (params?: { skip?: number; limit?: number; risk_level?: string }) =>
  api.get<TransactionDetail[]>('/api/transactions', { params }).then((r) => r.data);

export const getTransaction = (id: string) =>
  api.get<TransactionDetail>(`/api/transactions/${id}`).then((r) => r.data);

// Dashboard
export const getDashboardStats = () =>
  api.get<DashboardStats>('/api/dashboard/stats').then((r) => r.data);

export const getDashboardCharts = () =>
  api.get<DashboardCharts>('/api/dashboard/charts').then((r) => r.data);

// Investigations
export const listInvestigations = (params?: {
  skip?: number;
  limit?: number;
  status?: string;
  priority?: string;
  search?: string;
}) => api.get<Investigation[]>('/api/investigations', { params }).then((r) => r.data);

export const getInvestigation = (id: string) =>
  api.get<Investigation>(`/api/investigations/${id}`).then((r) => r.data);

export const reviewInvestigation = (
  id: string,
  data: { analyst_id: string; action: string; verdict?: string; comment?: string }
) => api.post<Investigation>(`/api/investigations/${id}/review`, data).then((r) => r.data);

export const addInvestigationNote = (
  id: string,
  data: { analyst_id: string; content: string; note_type: string }
) => api.post(`/api/investigations/${id}/notes`, data).then((r) => r.data);

export const getAuditHistory = (id: string) =>
  api.get(`/api/investigations/${id}/audit`).then((r) => r.data);

// Simulator
export const getCurrentThresholds = () =>
  api.get('/api/simulator/thresholds').then((r) => r.data);

export const runSimulation = (data: SimulatorInput) =>
  api.post<SimulatorResult>('/api/simulator/simulate', data).then((r) => r.data);

// Model
export const getModelEvaluation = (model?: string) =>
  api.get<ModelEvaluationReport>('/api/model/evaluation', { params: model ? { model_name: model } : {} }).then((r) => r.data);

export const getModelMonitoring = () =>
  api.get('/api/model/monitoring').then((r) => r.data);

export const triggerTraining = () =>
  api.post('/api/model/train').then((r) => r.data);
